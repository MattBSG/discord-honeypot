set /p token=Enter Token :
echo {>cred.json
echo %tab%"token":"%token%",>>cred.json
echo %tab%"userid":"%uid%">>cred.json
echo }>>cred.json
cd commands/Channels
echo {>uid.json
echo %tab%"userid":"%uid%">>uid.json
echo }>>uid.json
cd ..
cd DMs
echo {>uid.json
echo %tab%"userid":"%uid%">>uid.json
echo }>>uid.json
cd ..
cd x_x
echo {>uid.json
echo %tab%"userid":"%uid%">>uid.json
echo }>>uid.json
cd ..
cd ..