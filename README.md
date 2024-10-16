# Lawrencium

Lawrencium is simple and secure **bank**!
That project use **sha256**, **flask** and **sqlite3**.

## How it works?

First of all you have to sign up.
Then you get your [seed phrase](https://coinmarketcap.com/academy/en/glossary/seed).
In database will be recorded only your **public key** and **balance**.
If you wanna log in, you have to write your **seed phrase**, which will turn into a **public key** by hashing method, the **public key** will be verified in the database.
If such a key exists, the **funds** on it are at your disposal!
