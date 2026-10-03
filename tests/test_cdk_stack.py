import sys
import os

import aws_cdk as cdk
from aws_cdk.assertions import Template

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "infra", "cdk"))
from traceforge_stack import TraceForgeStack  # noqa: E402


def _synth_template():
    app = cdk.App()
    stack = TraceForgeStack(app, "TestStack")
    return Template.from_stack(stack)


def test_s3_bucket_is_kms_encrypted_and_blocks_public_access():
    template = _synth_template()
    template.has_resource_properties("AWS::S3::Bucket", {
        "PublicAccessBlockConfiguration": {
            "BlockPublicAcls": True,
            "BlockPublicPolicy": True,
            "IgnorePublicAcls": True,
            "RestrictPublicBuckets": True,
        },
    })
    template.resource_count_is("AWS::KMS::Key", 1)


def test_kinesis_stream_is_encrypted():
    template = _synth_template()
    template.has_resource_properties("AWS::Kinesis::Stream", {
        "StreamEncryption": {"EncryptionType": "KMS"},
    })


def test_ingestion_role_has_no_wildcard_admin_policy():
    template = _synth_template()
    policies = template.find_resources("AWS::IAM::Policy")
    for _, policy in policies.items():
        for stmt in policy["Properties"]["PolicyDocument"]["Statement"]:
            actions = stmt.get("Action")
            actions = actions if isinstance(actions, list) else [actions]
            assert "*" not in actions, f"found wildcard action in {stmt}"
