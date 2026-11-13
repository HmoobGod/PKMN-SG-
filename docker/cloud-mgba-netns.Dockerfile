FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -qq && apt-get install --no-install-recommends -y python3 mgba-sdl xvfb xauth ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /lab
COPY tools /lab/tools
ENV PYTHONDONTWRITEBYTECODE=1
CMD ["sh","-c","python3 -m unittest discover -s /lab/tools -p 'test_cloud_rsp_netns_gate.py' -v && xvfb-run -a -s '-screen 0 640x480x24' python3 /lab/tools/cloud_rsp_netns_fixture.py"]
