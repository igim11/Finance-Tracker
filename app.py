import datetime

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request

app = Flask(__name__)

db = SQL("sqlite:///tracker.db")

app.secret_key = '12345'

def numeric(value):
    """Format value as accounting."""
    return f"{value:,.2f}"

@app.route("/")
def accounts():

    # display database on page
    accounts = db.execute("SELECT * FROM accounts")

    total = 0

    for row in accounts:
        account_name = row["account_name"]
        balance = row["balance"]
        total += balance
        row["balance"] = numeric(balance)

    total = numeric(total)

    return render_template("accounts.html", accounts=accounts, total=total)


@app.route("/add_account", methods=["GET", "POST"])
def add_account():

    accountname = request.form.get("accountname")
    balance = request.form.get("balance")

    # check if account name is empty
    if not accountname:
        flash("Input an Account Name")
        return redirect("/")

    # check if balance is zero
    if balance == "":
        balance = 0

    # add account into database
    db.execute("INSERT INTO accounts (account_name, balance) VALUES (?, ?)", accountname, balance)

    flash("Account Successfully Added")
    return redirect("/")


@app.route("/delete_account", methods=["GET", "POST"])
def delete_account():

    db.execute("DELETE FROM accounts WHERE account_name == ?", request.form.get("accountname"))

    flash("Account Deleted")
    return redirect("/")


@app.route("/edit_account_name", methods=["GET", "POST"])
def edit_account_name():

    accountname = request.form.get("accountname")
    newname = request.form.get("newname")

    # check if account name is empty
    if not newname:
        flash("Input an Account Name")
        return redirect("/")

    db.execute("UPDATE accounts SET account_name = ? WHERE account_name == ?", newname, accountname)

    flash("Account Successfully Edited")
    return redirect("/")

@app.route("/edit_account_balance", methods=["GET", "POST"])
def edit_account_balance():

    accountname = request.form.get("accountname")
    newbalance = request.form.get("newbalance")

    # check if balance is zero
    if newbalance == "":
        newbalance = 0

    db.execute("UPDATE accounts SET balance = ? WHERE account_name == ?", newbalance, accountname)

    flash("Account Successfully Edited")
    return redirect("/")


@app.route("/log", methods=["GET","POST"])
def log():

    if request.method == "GET":

        # display transactions on page
        transactions = db.execute("SELECT * FROM transactions ORDER BY date DESC, log_timestamp DESC")

        for row in transactions:
            amount = row["amount"]
            row["amount"] = numeric(amount)

        # display accounts in dropdown menu
        accounts = db.execute("SELECT * FROM accounts")

        return render_template("log.html", transactions=transactions, accounts=accounts)

    else:

        date = request.form.get("date")
        transactiontype = request.form.get("transactiontype")
        expensetype = request.form.get("expensetype")
        description = request.form.get("description")
        toaccount = request.form.get("toaccount")
        fromaccount = request.form.get("fromaccount")
        amount = request.form.get("amount")
        timestamp = datetime.datetime.now()

        # clears 'from account' field for non compatible transaction types
        if transactiontype == "Transfer" or transactiontype == "Lend" or transactiontype == "Payback":
            fromaccount = fromaccount
        else:
            fromaccount = ""

        # clears 'expense type' field for non compatible transaction types
        if transactiontype != "Expense":
            expensetype = ""

        # Ensures Transaction Type field is not empty
        if not transactiontype:
            flash("Input a Transaction Type")
            return redirect("/log")

        # Ensures Date field is not empty
        if not date:
            flash("Input Date")
            return redirect("/log")

        # Ensures To Account field is not empty
        if not toaccount:
            flash("Select an Account")
            return redirect("/log")

        # Ensures Amount field is not empty
        if not amount:
            flash("Input an amount")
            return redirect("/log")

        # Ensures Expense Type field is not empty if Expense
        if transactiontype == "Expense":
            if not expensetype:
                flash("Input Expense Type")
                return redirect("/log")

        # Ensures From Account field is not empty if transfer, lend, or payback
        if transactiontype == "Transfer" or transactiontype == "Lend" or transactiontype == "Payback":
            if not fromaccount:
                flash("Input from what Account")
                return redirect("/log")

        # Ensures amount is added to account if income
        if transactiontype == "Income":
            toaccountcash = db.execute("SELECT balance FROM accounts WHERE account_name == ?", toaccount)[0]["balance"]
            updatedtoaccountcash = float(toaccountcash) + float(amount)

            db.execute("UPDATE accounts SET balance = ? WHERE account_name = ?", updatedtoaccountcash, toaccount)

        # Ensures amount is subtracted to account if expense
        elif transactiontype == "Expense":
            toaccountcash = db.execute("SELECT balance FROM accounts WHERE account_name == ?", toaccount)[0]["balance"]
            updatedtoaccountcash = float(toaccountcash) - float(amount)

            db.execute("UPDATE accounts SET balance = ? WHERE account_name = ?", updatedtoaccountcash, toaccount)

        # Ensures amount is subtracted from account and added to receivables if lending
        elif transactiontype == "Transfer" or transactiontype == "Lend" or transactiontype == "Payback" or transactiontype == "Invest":
            toaccountcash = db.execute("SELECT balance FROM accounts WHERE account_name == ?", toaccount)[0]["balance"]
            fromaccountcash = db.execute("SELECT balance FROM accounts WHERE account_name == ?", fromaccount)[0]["balance"]
            updatedtoaccountcash = float(toaccountcash) + float(amount)
            updatedfromaccountcash = float(fromaccountcash) - float(amount)

            db.execute("UPDATE accounts SET balance = ? WHERE account_name = ?", updatedtoaccountcash, toaccount)
            db.execute("UPDATE accounts SET balance = ? WHERE account_name = ?", updatedfromaccountcash, fromaccount)

        # Ensures amount is subtracted from account and added to receivables if lending
        elif transactiontype == "Borrow":
            toaccountcash = db.execute("SELECT balance FROM accounts WHERE account_name == ?", toaccount)[0]["balance"]
            updatedtoaccountcash = float(toaccountcash) - float(amount)

            db.execute("UPDATE accounts SET balance = ? WHERE account_name = ?", updatedtoaccountcash, toaccount)


        # add transaction into database
        db.execute("INSERT INTO transactions (transaction_type, expense_type, date, description, to_account, from_account, amount, log_timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    transactiontype, expensetype, date, description, toaccount, fromaccount, amount, timestamp)

        flash("Transaction Successfully Logged")
        return redirect("/log")


@app.route("/stats")
def stats():

    expenses = db.execute("SELECT expense_type, amount FROM transactions WHERE transaction_type == 'Expense'")
    accounts = db.execute("SELECT account_name, balance FROM accounts WHERE balance > 0")

    return render_template("stats.html", expenses=expenses, accounts=accounts)