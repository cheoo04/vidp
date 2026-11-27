FROM httpd:2.4
COPY index.html /usr/local/apache2/htdocs/index.html
COPY vidp.conf /usr/local/apache2/conf/extra/vidp.conf
RUN echo "Include conf/extra/vidp.conf" >> /usr/local/apache2/conf/httpd.conf
# Adresse du load balancer (surchargée par docker compose / Ansible)
ENV LB_URL=http://lb:80
