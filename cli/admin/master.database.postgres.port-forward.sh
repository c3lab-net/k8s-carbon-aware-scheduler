#!/bin/sh

kubectl port-forward service/cas-master-database 5432:5432
