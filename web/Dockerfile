FROM amsterdam/python
MAINTAINER datapunt@amsterdam.nl

ENV PYTHONUNBUFFERED 1

EXPOSE 8000

RUN adduser --system datapunt \
	&& mkdir -p /static \
	&& chown datapunt /static \
	&& mkdir -p /app/unzipped \
	&& chown datapunt /app/unzipped \
	&& mkdir -p /app/data \
	&& chown datapunt /app/data \
	&& pip install uwsgi

WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt

USER datapunt

COPY handelsregister /app/
COPY .jenkins-import /.jenkins-import/


CMD ["/app/docker-run.sh"]
