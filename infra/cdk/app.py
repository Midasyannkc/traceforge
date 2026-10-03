#!/usr/bin/env python3
import aws_cdk as cdk
from traceforge_stack import TraceForgeStack

app = cdk.App()
TraceForgeStack(app, "TraceForgeStack")
app.synth()
