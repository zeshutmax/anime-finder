FROM python:3.10.4-alpine
RUN pip install --upgrade pip
WORKDIR /
COPY . /

RUN pip install -r requirements.txt
 
ENTRYPOINT ["python"]
CMD ["app.py"]