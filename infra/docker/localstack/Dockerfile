FROM localstack/localstack:latest

COPY infra/docker/localstack-init /etc/localstack/init/ready.d
RUN chmod +x /etc/localstack/init/ready.d/init-aws.sh

