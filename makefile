apply:
	kubectl apply -f rabbitmq/rabbitmq-deployment.yaml
	kubectl apply -f rabbitmq/rabbitmq-service.yaml

	kubectl port-forward --address 0.0.0.0 service/rabbitmq 5672:5672 &