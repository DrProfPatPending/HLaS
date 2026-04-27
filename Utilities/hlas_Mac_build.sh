#!/bin/bash
# Move to the appropriate directory
cd /Users/rob.scoffin/hlas
echo "Rebuilding latest HLaS from Github sources"

echo "Pulling latest code from Git"
git pull origin main

echo "Build Mac frontend using Capacitor"
cd frontend
npm install
npm run build
npx cap sync ios
cd ..

echo "Now Check Build..."

