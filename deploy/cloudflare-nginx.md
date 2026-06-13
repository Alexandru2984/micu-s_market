# Cloudflare + Nginx deployment notes

Recommended chain:

Cloudflare -> public Nginx/vhost -> optional internal Nginx/vhost -> Gunicorn socket

Rules:

- Use Cloudflare SSL/TLS mode `Full (strict)` with a valid origin certificate.
- Block direct origin access where possible. Allow Cloudflare IP ranges at the edge firewall or Nginx layer.
- The public-facing Nginx server must overwrite, not forward, client-supplied proxy headers.
- If there is another internal vhost before Gunicorn, only that trusted internal hop may preserve the already-trusted scheme. Do not preserve `X-Forwarded-Proto` on a public listener.
- Set `DJANGO_USE_X_FORWARDED_PROTO=True` only after the final proxy in front of Gunicorn sets `X-Forwarded-Proto` correctly.
- Set `DJANGO_TRUSTED_PROXY_CHAIN_CONFIGURED=True` only after verifying the full chain.
- Do not serve `/media/chat/private/` from Nginx. Those files are served by Django through an authorization check.

Required `.env` values for the current domain:

```env
DJANGO_ALLOWED_HOSTS=market.micutu.com
CSRF_TRUSTED_ORIGINS=https://market.micutu.com
DJANGO_USE_X_FORWARDED_PROTO=True
DJANGO_TRUSTED_PROXY_CHAIN_CONFIGURED=True
```

Public-facing Nginx should use this shape:

```nginx
server {
    listen 443 ssl http2;
    server_name market.micutu.com;

    client_max_body_size 25M;

    location /static/ {
        alias /home/micu/Micu_market/staticfiles/;
    }

    location ^~ /media/chat/private/ {
        return 404;
    }

    location /media/ {
        alias /home/micu/Micu_market/media/;
    }

    location / {
        proxy_pass http://unix:/home/micu/Micu_market/gunicorn.sock;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_redirect off;
    }
}
```

If an internal Nginx vhost sits between the public vhost and Gunicorn, restrict that internal listener to the public vhost IP/socket and then set:

```nginx
proxy_set_header X-Forwarded-Proto $http_x_forwarded_proto;
```

Only do this on the internal listener. On an internet-facing listener, always overwrite with `$scheme`.
