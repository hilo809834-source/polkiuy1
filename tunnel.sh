#!/bin/bash
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -R 80:localhost:9000 serveo.net
