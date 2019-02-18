# Deadline Reminder Bot

Reminder line bot using [Flask](http://flask.pocoo.org/). This bot functions to remind you of your deadlines by chatting you to make sure that you don't miss them.

## How To Use

Tutorial ini akan menunjukkan cara agar anda dapat melakukan deploy terhadap project ini

### Prerequisites

1. Python
2. Postgresql
3. Python libraries (flask, psycopg2, linebotsdk, etc)
4. Heroku account
5. Github account
6. Line channel
7. CronJobs account

### Deploy the Project

Untuk menggunakan bot ini, silahkan upload files program ke github  dan deploy ke heroku. Setelah itu lakukan konfigurasi agar program yang  telah di deploy dapat terhubung pada line channel.

## 

## Running the Program

Silahkan add bot pada line dan bot akan otomatis mendaftarkan akun line anda kedalam sistem. Untuk dapat running maka berikan configurasi cronjobs pada saat tertentu sesuai kebutuhan anda.



## Chat interaction

1. /showall
   Perintah *showall* akan membuat bot menampilkan jadwal yang pernah anda daftarkan.
2. /add "<deskripsi deadline>" "<dd mm yyyy hh:mm>"
   Perintah diatas akan membuat bot mendaftarkan deadline anda dan mengingatkan pada waktu sesuai yang di set di cronjobs.