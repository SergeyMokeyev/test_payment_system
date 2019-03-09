FROM python

COPY ./ /opt/server/
WORKDIR /opt/server/
RUN pip3 install -r requirements.txt
