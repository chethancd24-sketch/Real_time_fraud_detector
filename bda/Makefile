.PHONY: setup data test producer dashboard train

setup:
	python -m venv .venv
	.venv/Scripts/python -m pip install --upgrade pip
	.venv/Scripts/python -m pip install -r requirements.txt

data:
	python data/generate_data.py

train:
	python ml/train.py

test:
	pytest -m "not integration"

producer:
	python producers/kafka_producer.py --speed 10 --count 1000

dashboard:
	streamlit run dashboard/app.py
