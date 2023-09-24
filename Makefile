.PHONY: set-permissions install-poetry setup-venv install-deps run setup

# Set the appropriate ownership and permissions
set-permissions:
	@sudo chown -R ec2-user:ec2-user ./
	@sudo chmod -R 755 ./

# Install poetry if not already installed
install-poetry:
	@if ! command -v poetry &> /dev/null; then \
		curl -sSL https://install.python-poetry.org | python3; \
	fi

# Set up a virtual environment using poetry
setup-venv:
	@if [ ! -d ".venv" ]; then \
		python3 -m venv .venv; \
		poetry config virtualenvs.in-project true; \
	fi
	@. .venv/bin/activate

# Install python dependencies
install-deps:
	@poetry install

# Run the application
run:
	@poetry run python main_data_collect.py $(WRITER_TYPE_ARG) $(BUFFER_SIZE_ARG) $(SLEEP_DURATION_ARG)

# Combined target for the entire setup and run
setup: set-permissions install-poetry setup-venv install-deps run

