# Convenience targets for JupyterLab exploration

IMAGE_JUPYTER ?= edge-ai-data:jupyter

.PHONY: build-jupyter lab lab-detach stop ps

build-jupyter:
	docker build -f Dockerfile.jupyter -t $(IMAGE_JUPYTER) .

lab: build-jupyter
	docker run --rm -it -p 8888:8888 -v $(PWD):/work $(IMAGE_JUPYTER) \
	  jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --NotebookApp.token= --NotebookApp.password=

lab-detach: build-jupyter
	docker run -d --name edge-ai-lab -p 8888:8888 -v $(PWD):/work $(IMAGE_JUPYTER) \
	  jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --NotebookApp.token= --NotebookApp.password=

stop:
	-docker rm -f edge-ai-lab

ps:
	docker ps --filter name=edge-ai-lab


.PHONY: vision-image vision-video
vision-image:
	python -m vision.pipelines.image_recognition --input ./data/media/images --out ./data/samples/hot/vision

vision-video:
	python -m vision.pipelines.video_recognition --input ./data/media/video/sample.mp4 --out ./data/samples/hot/vision --every_ms 500


.PHONY: vision-image-annotate vision-video-annotate
vision-image-annotate:
	python -m vision.pipelines.image_recognition --input ./data/media/images --out ./data/samples/hot/vision --annotate --frames_out ./data/samples/hot/vision/frames

vision-video-annotate:
	python -m vision.pipelines.video_recognition --input ./data/media/video/sample.mp4 --out ./data/samples/hot/vision --every_ms 500 --annotate --frames_out ./data/samples/hot/vision/frames


.PHONY: manifest-vision
manifest-vision:
	python tools/update_manifest.py --data-root . --outdir ./data/samples/hot/vision --site A --device D --topic vision


.PHONY: anchor-testnet verify-anchor
anchor-testnet:
	python tools/anchor_bitcoin.py --manifest $(MANIFEST) --network testnet --rpc-url $(RPC_URL) --rpc-user $(RPC_USER) --rpc-pass $(RPC_PASS) --wallet $(WALLET) --fee-satvB 10

verify-anchor:
	python tools/verify_anchor.py --manifest $(MANIFEST) --network testnet --rpc-url $(RPC_URL) --rpc-user $(RPC_USER) --rpc-pass $(RPC_PASS) --wallet $(WALLET)
