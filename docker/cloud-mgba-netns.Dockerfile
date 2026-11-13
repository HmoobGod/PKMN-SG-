FROM ubuntu:26.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -qq && apt-get install --no-install-recommends -y python3 mgba-sdl xvfb xauth && rm -rf /var/lib/apt/lists/*
ENV PATH="/usr/games:${PATH}"
WORKDIR /lab
COPY tools /lab/tools
ENV PYTHONDONTWRITEBYTECODE=1
ENV HOME=/tmp
USER 65534:65534
CMD ["sh","-c","python3 /lab/tools/cloud_mgba_pkg_gate.py && mgba --version && sha256sum $(command -v mgba) && python3 -m unittest discover -s /lab/tools -p 'test_*.py' -v && xvfb-run -a -s '-screen 0 640x480x24' python3 /lab/tools/cloud_rsp_combined_fixture.py && xvfb-run -a -s '-screen 0 640x480x24' python3 /lab/tools/cloud_rsp_thumb2_fixture.py && timeout -k 3s 50s xvfb-run -a -s '-screen 0 640x480x24' python3 /lab/tools/cloud_rsp_thumb_hit_fixture.py && timeout -k 3s 50s xvfb-run -a -s '-screen 0 640x480x24' python3 /lab/tools/cloud_rsp_thumb_qsupported_fixture.py"]
