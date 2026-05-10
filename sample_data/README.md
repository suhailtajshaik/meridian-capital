# sample_data/

Seed CSVs for the Meridian demo. Upload any of these in the **Documents**
tab to populate the advisor's knowledge base.

## Persona: Alex Rivera

Single working professional. **$4,000/month take-home income**. Three small
debts under $10,000 total — all the math works in your head on stage.

## Core demo set

| File | Rows | Description |
| --- | ---: | --- |
| `chase_checking_apr2026.csv` | 13 | April checking — $4,000 income, $2,450 expenses, $1,550 surplus |
| `capital_one_apr2026.csv` | 9 | April credit card — $1,000 closing, 24.99% APR, $20 interest, $50 minimum-only payment |
| `sofi_student_loan_apr.csv` | 1 | SoFi student loan — $3,000 @ 5% APR, $100/mo |
| `honda_auto_loan.csv` | 24 | Honda Financial auto loan — $5,000 starting balance, 6% APR, $200/mo amortization |

**Total demo debt: $9,000** (under $10K — easy round numbers).

## Optional extras

| File | Rows | Description |
| --- | ---: | --- |
| `wells_mortgage_q1.csv` | 1 | Wells Fargo mortgage — $312,400 @ 5.875%. Bigger demo (adds property liability). Skip for the simple story. |
| `schwab_brokerage_q1.csv` | 18 | Schwab brokerage holdings & Q1 activity. Useful for the Savings advisor. |

## April reconciliation (Chase)

| Flow | Amount |
| --- | ---: |
| Opening balance | $1,000 |
| + April paycheck | +$4,000 |
| − Rent | −$1,500 |
| − Auto loan (Honda) | −$200 |
| − Student loan (SoFi) | −$100 |
| − Utilities | −$100 |
| − Groceries | −$200 |
| − Dining out | −$100 |
| − Subscriptions | −$50 |
| − Transport | −$100 |
| − Entertainment | −$50 |
| − CC minimum payment | −$50 |
| **Closing balance** | **$2,550** |

Net surplus = $4,000 − $2,450 = **$1,550/month**.

## Capital One — the credit card treadmill story

| Step | Amount |
| --- | ---: |
| Previous balance | $850 |
| New charges (April) | +$180 |
| Payment received | −$50 |
| Interest @ 24.99% APR | +$20 |
| **Closing balance** | **$1,000** |

The story: minimum $50 payment − $20 interest = $30 principal pay-down. At this
rate, a $1,000 balance takes **~36 months** to pay off and costs ~$200 in
interest. **Avalanche it.**

## Total liabilities snapshot

| Debt | Balance | APR | Min/mo |
| --- | ---: | ---: | ---: |
| Capital One | $1,000 | 24.99% | $50 |
| Honda Auto Loan | $4,825 | 6.00% | $200 |
| SoFi Student Loan | $3,000 | 5.00% | $100 |
| **Total** | **$8,825** | | **$350** |

Weighted APR: ~9.0%. Highest priority: Capital One.

## Column schemas

- **Checking:** `date, description, amount, category, balance`
- **Credit card:** `date, description, amount, category, balance_owed`
- **Debt statement:** `statement_date, balance, apr, monthly_payment, interest_portion, principal_portion, next_due, lender`
- **Amortization:** `payment_date, payment, interest, principal, remaining_balance`
