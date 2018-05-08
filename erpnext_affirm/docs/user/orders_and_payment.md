# Orders and Payments

## Why is the payment status Unpaid?

The moment the order is placed, Affirm confirms the amount but won't forward the payment to JH Audio. We need to first 'capture' the payment to tell Affirm to forward the payment to us. 

---

## How and when to capture a payment?

We need to capture the payment when the order item(s) are ready to go into production.

To capture a payment, go to the respective sales order and click on the capture button on the top-right.

![Screen Shot 2018-03-12 at 4.29.10 PM.png](https://files.nuclino.com/files/1ba8f6b4-ba93-4f13-9e47-8403c001b3ba/Screen Shot 2018-03-12 at 4.29.10 PM.png)

* Once you click on the button, the system will check with Affirm and confirm the payment.
* The process will take some time and the screen will freeze during the same (approx. 2 to 5 seconds).
* Once it's confirmed, you will receive a payment capture success message.
* The payment status will change to 'Paid' and a Payment Entry will be created by the system.

---

## What happens when you capture the payment?

* When you capture the payment, Affirm forwards the sales order amount to your bank.
* The customer gets a SMS from Affirm stating that their payment was captured by JH Audio.
* The customer's EMI cycle starts from this date. They will receive their first invoice for payment a month after this day.

**Important Pointer - You need to capture the payment within 30 days from the order being placed to prevent it from lapsing.**

---

## How to check Affirm orders?

On the left sidebar, select the "Affirm" filter to list all Affirm orders. You can also manually apply a filter where `payment method = affirm`.

![Screen Shot 2018-03-12 at 4.32.35 PM.png](https://files.nuclino.com/files/78f6b3ee-f4d1-4c46-be39-ddc42c48d94e/Screen Shot 2018-03-12 at 4.32.35 PM.png)

---

## What internal emails are sent for affirm orders?

3 reminder emails are sent from the system.

* The first one is sent when the order is placed. Check the email alert for **"A new order was placed through Affirm"**.
* The second one is sent 15 days after the order was placed, but only if the payment has not been captured - check **"An Affirm order is pending (15 days since transaction)"**.
* The third and final reminder is sent 25 days after the order was placed, but only if the payment has not been captured - check **"An Affirm order is pending (25 days since transaction)"**.