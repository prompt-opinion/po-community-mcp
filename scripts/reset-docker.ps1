cd ../
docker compose -f docker-compose-local.yml down -v --rmi all
docker compose -f docker-compose-local.yml up -d
cd -