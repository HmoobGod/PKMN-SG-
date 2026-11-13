FROM ubuntu:26.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -qq && apt-get install --no-install-recommends -y python3 mgba-sdl xvfb xauth && rm -rf /var/lib/apt/lists/*
ENV PATH="/usr/games:${PATH}"
WORKDIR /lab
COPY tools /lab/tools
ENV PYTHONDONTWRITEBYTECODE=1
ENV HOME=/tmp
USER 65534:65534
CMD ["sh","-c","python3 /lab/tools/cloud_mgba_pkg_gate.py && python3 -m unittest discover -s /lab/tools -p 'test_pr26_generated_real_mgba_runner.py' -v && timeout -k 3s 50s xvfb-run -a -s '-screen 0 640x480x24' python3 /lab/tools/pr26_generated_real_mgba_runner.py"]
