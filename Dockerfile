FROM hwiyoung/opensfm:220912

RUN apt-get update
RUN apt install -y gdal-bin pdal libpdal-dev python3-pdal

RUN pip install numpy --upgrade
RUN pip install pyexiv2 numba rich pandas scipy pdal

COPY ./module /code/module
COPY ./tests /code/tests
COPY ./run.py /code

WORKDIR /code