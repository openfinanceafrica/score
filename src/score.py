from typing import List
from datetime import timedelta, datetime, timezone
from score_types import PaymentStatus, Score, ScoreError, ScoreInput, ScoredMonth
from dateutil import parser

from constants import (
    PREVIOUS_PAYMENTS_BONUS_COEFFICIENT,
    SCORE_COEFFICIENT,
    TIME_BONUS_AFTER_DUE_DATE_COEFFICIENT,
    TIME_BONUS_COEFFICIENT,
)


def getScore(scoreInput: ScoreInput) -> Score:
    """Form a complex number.

    Keyword arguments:
    real -- the real part (default 0.0)
    imag -- the imaginary part (default 0.0)
    """

    paymentStartDate = parser.isoparse(scoreInput["paymentStartDate"])
    start = paymentStartDate
    paymentEndDate = (
        parser.isoparse(scoreInput["paymentEndDate"])
        if scoreInput.get("paymentEndDate")
        else datetime.now(timezone.utc)
    )
    expectedPaymentDay = scoreInput["expectedPaymentDay"]
    expectedPaymentAmount = scoreInput["expectedPaymentAmount"]
    totalScore = 0
    expectedPayments = 0
    scoredMonths: List[ScoredMonth] = []
    overallScore = 0
    paidStreak = 0
    longestPaidStreak = 0
    overDueStreak = 0
    longestOverDueStreak = 0
    balance = 0

    # We need to ensure that we are consistently using timezone aware dates so we don't get the error:
    # "can't compare offset-naive and offset-aware datetimes"
    # If timezone info isn't included in a date within the request the it's assumed to be UTC.
    if (
        paymentStartDate.tzinfo is None
        or paymentStartDate.tzinfo.utcoffset(paymentStartDate) is None
    ):
        paymentStartDate = paymentStartDate.astimezone()
        start = paymentStartDate
    if (
        paymentEndDate.tzinfo is None
        or paymentEndDate.tzinfo.utcoffset(paymentEndDate) is None
    ):
        paymentEndDate = paymentEndDate.astimezone()

    # If paymentStartDate is still in the future and scoreBeforeStartDate isn't specified in the request,
    # we'll exit immediately. It's not necessarily an error but we want users to explicitly say whether
    # they want to score future dates.
    if datetime.now(timezone.utc) < paymentStartDate and not scoreInput.get(
        "scoreBeforeStartDate"
    ):
        return {
            "overallScore": overallScore,
            "paidStreak": 0,
            "balance": 0,
            "overDueStreak": 0,
            "scoredMonths": scoredMonths,
            "expectedPaymentAmount": expectedPaymentAmount,
            "error": ScoreError.START_DATE_IN_FUTURE.name,
        }
    while start <= paymentEndDate:
        if expectedPaymentDay == start.day:
            expectedPayments += expectedPaymentAmount
            lastPaymentDate = None
            actualPayments = 0
            balancePaymentDateAfterDueDate = None
            actualPaymentsAfterDueDate = 0

            for payment in scoreInput["payments"]:
                # Get the actual total payments made before or on the due date and also keep track of the
                # last payment date (the earlier the payment, the better if balance is paid off)
                if parser.isoparse(payment["date"]) <= start:
                    actualPayments += int(payment["amount"])
                    lastPaymentDate = parser.isoparse(payment["date"])
                # Get the date when the balance was paid. The delta between the due date and the time the balance was
                # paid off will be a factor in scoring.
                else:
                    actualPaymentsAfterDueDate += int(payment["amount"])
                    if (
                        (actualPayments + actualPaymentsAfterDueDate) - expectedPayments
                    ) >= 0:
                        balancePaymentDateAfterDueDate = parser.isoparse(
                            payment["date"]
                        )
                        break

            scoredMonth = getScoredMonth(
                expectedPaymentAmount,
                actualPayments,
                expectedPayments,
                start,
                lastPaymentDate,
                balancePaymentDateAfterDueDate,
            )

            scoredMonths.append(scoredMonth)
            totalScore += scoredMonth["score"]
            balance = scoredMonth["balance"]

        start = start + timedelta(days=1)

    for scoredMonth in scoredMonths:
        if (
            scoredMonth["status"] == PaymentStatus.PAID.name
            or scoredMonth["status"] == PaymentStatus.OVERPAID.name
        ):
            paidStreak += 1
            overDueStreak = 0

        if scoredMonth["status"] == PaymentStatus.OVERDUE.name:
            overDueStreak += 1
            paidStreak = 0

        if paidStreak > longestPaidStreak:
            longestPaidStreak = paidStreak

        if overDueStreak > longestOverDueStreak:
            longestOverDueStreak = overDueStreak

    # Limit overall score to 1
    if len(scoredMonths) > 0:
        overallScore = (
            1
            if round(totalScore / len(scoredMonths), 2) > 1
            else round(totalScore / len(scoredMonths), 2)
        )

    result = {
        "overallScore": overallScore,
        "balance": balance,
        "paidStreak": longestPaidStreak,
        "overDueStreak": longestOverDueStreak,
        "scoredMonths": scoredMonths,
        "expectedPaymentAmount": expectedPaymentAmount,
    }

    if len(scoredMonths) < 1:
        result["error"] = ScoreError.NO_SCORED_MONTHS.name

    return result


def getScoredMonth(
    expectedPaymentAmount: int,
    amountPaid: int,
    expectedPayments: int,
    dueDate: datetime,
    lastPaymentDate: datetime,
    balancePaymentDateAfterDueDate: datetime,
) -> ScoredMonth:
    """Form a complex number.

    Keyword arguments:
    real -- the real part (default 0.0)
    imag -- the imaginary part (default 0.0)
    """

    score = None
    status = PaymentStatus.UNKNOWN.name

    balance = amountPaid - expectedPayments

    if not lastPaymentDate:
        return {
            score: 0,
            status: PaymentStatus.OVERDUE.name,
            dueDate: dueDate,
            balance: balance,
        }

    # Get a time bonus based on how early the payment was made before the due date
    timeBonus = 0
    if lastPaymentDate < dueDate:
        # need to use 'total_seconds' rather than 'days' for accuracy
        days = (dueDate - lastPaymentDate).total_seconds() / (24 * 60 * 60)
        timeBonus = round(days * TIME_BONUS_COEFFICIENT, 2)

    if balance == 0:
        score = 1
        score = score
        status = PaymentStatus.PAID.name

    if balance > 0:
        score = 1 + (balance / expectedPaymentAmount) * SCORE_COEFFICIENT
        score = score
        status = PaymentStatus.OVERPAID.name

    if balance < 0:
        score = 0
        status = PaymentStatus.OVERDUE.name
        # Get a time bonus based on how early the payment was made after the due date
        if balancePaymentDateAfterDueDate:
            # need to use 'total_seconds' rather than 'days' for accuracy
            days = (balancePaymentDateAfterDueDate - dueDate).total_seconds() / (
                24 * 60 * 60
            )
            timeBonus = round(1 - (days * TIME_BONUS_AFTER_DUE_DATE_COEFFICIENT), 2)
            if timeBonus < 0:
                timeBonus = 0

    if score == None:
        print("Score could not be calculated. Balance: %s" % balance)
        return {
            score: -1,
            status: PaymentStatus.UNKNOWN.name,
            dueDate: dueDate,
            balance: balance,
        }

    score = score + timeBonus

    # If the score is 0 we'll give credit for previous payments made
    if score == 0:
        overallPaymentsBonus = (
            amountPaid / expectedPayments
        ) * PREVIOUS_PAYMENTS_BONUS_COEFFICIENT
        score += overallPaymentsBonus

    score = round(score, 2)

    return {
        "score": score,
        "status": status,
        "dueDate": dueDate.isoformat(),
        "balance": balance,
    }
