aws bedrock create-evaluation-job \
  --job-name "eval-correctness-$(date +%s)" \
  --role-arn "arn:aws:iam::231295109082:role/bedrock-eval-role" \
  --evaluation-config '{"automated":{"datasetMetricConfigs":[{"taskType":"General","dataset":{"name":"agentcore-eval-dataset","datasetLocation":{"s3Uri":"s3://udacity-agentic-engineer-c1-eval-231295109082/output_eval_dataset.jsonl"}},"metricNames":["Builtin.Correctness"]}],"evaluatorModelConfig":{"bedrockEvaluatorModels":[{"modelIdentifier":"amazon.nova-pro-v1:0"}]}}}' \
  --inference-config '{"models":[{"precomputedInferenceSource":{"inferenceSourceIdentifier":"my-support-chatbot"}}]}' \
  --output-data-config '{"s3Uri":"s3://udacity-agentic-engineer-c1-eval-231295109082/evaluation-results/"}' \
  --region us-east-1
