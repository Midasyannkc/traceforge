"""
Real AWS CDK (Python) stack definition for the TraceForge platform:
S3 data lake bucket (Iceberg warehouse target), a KMS key encrypting it,
a Kinesis stream for agent telemetry, and a least-privilege IAM role for
the ingestion Lambda. Synthesized locally with the real `cdk` CLI
(`cdk synth`, no AWS credentials required); `cdk deploy` would require a
live account, which this sandbox does not have (see data/bronze/SOURCE.md).
"""
from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_s3 as s3,
    aws_kms as kms,
    aws_kinesis as kinesis,
    aws_iam as iam,
)
from constructs import Construct


class TraceForgeStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        encryption_key = kms.Key(
            self, "TraceForgeDataKey",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.RETAIN,
        )

        data_lake_bucket = s3.Bucket(
            self, "AgentInteractionsBucket",
            bucket_name=None,  # CDK-generated, avoids global-name collisions
            encryption=s3.BucketEncryption.KMS,
            encryption_key=encryption_key,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            versioned=True,
            removal_policy=RemovalPolicy.RETAIN,
        )

        telemetry_stream = kinesis.Stream(
            self, "AgentTelemetryStream",
            stream_name="traceforge-telemetry",
            shard_count=1,
            encryption=kinesis.StreamEncryption.KMS,
            encryption_key=encryption_key,
        )

        # least-privilege ingestion role: write-only to this bucket's
        # agent_interactions/ prefix, put-record-only to this stream,
        # decrypt-only (never full kms:*) on this key
        ingestion_role = iam.Role(
            self, "IngestionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )
        data_lake_bucket.grant_write(ingestion_role, "agent_interactions/*")
        telemetry_stream.grant_write(ingestion_role)
        encryption_key.grant_encrypt_decrypt(ingestion_role)

        self.data_lake_bucket = data_lake_bucket
        self.telemetry_stream = telemetry_stream
        self.ingestion_role = ingestion_role
