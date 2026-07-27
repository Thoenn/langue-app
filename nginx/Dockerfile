FROM nginx:alpine

RUN apk add --no-cache apache2-utils

COPY default.conf /etc/nginx/conf.d/default.conf

# Create htpasswd file with admin/GdPCID19405$*
RUN htpasswd -bc /etc/nginx/.htpasswd admin 'GdPCID19405$*'
