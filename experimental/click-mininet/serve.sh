{ echo "HTTP/1.0 200 OK\r\n\r\n"; cat serve.file; } | nc -l 80 &
