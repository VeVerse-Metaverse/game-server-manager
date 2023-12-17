FROM flant/shell-operator:latest

# Install python
ENV PYTHONUNBUFFERED=1
RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python

# Install and update pip
RUN python -m ensurepip
RUN /usr/bin/python -m pip install --upgrade pip

# Add and install requirements
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# Add hooks and scripts
COPY hooks /hooks
COPY main /main

# Convert line endings to linux for all python files to fix any line-ending issues
RUN apk add dos2unix --update-cache --repository http://dl-3.alpinelinux.org/alpine/edge/community/ --allow-untrusted
RUN dos2unix /hooks/*
RUN dos2unix /main/*

RUN chmod +x /hooks/00-watch-game-server-added.py
RUN chmod +x /hooks/10-watch-game-server-removed.py

RUN chmod +x /main/create-game-server-resource.py
RUN chmod +x /main/delete-game-server-resource.py
