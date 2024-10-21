FROM nginx:latest

RUN rm /etc/nginx/conf.d/default.conf /etc/nginx/nginx.conf
COPY /nginx.conf /etc/nginx/nginx.conf

COPY /static /usr/src/app/static
RUN mkdir -p /usr/src/app/static/media
