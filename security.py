import random
import string
from datetime import datetime, timedelta

from database import query, execute, hash_pin


def verify_login(employee_code, pin):

    employee_code = employee_code.upper().strip()

    users = query(
        """
        SELECT *
        FROM employees
        WHERE employee_code=?
        AND status='Active'
        """,
        (employee_code,)
    )

    if users.empty:
        return None

    user = users.iloc[0]

    if hash_pin(pin) == user["pin_hash"]:
        return user

    return None


def create_login_log(
    employee_id,
    employee_code,
    status="SUCCESS",
    ip_address="",
    device=""
):

    execute(
        """
        INSERT INTO login_logs
        (
            employee_id,
            employee_code,
            login_time,
            ip_address,
            device,
            status
        )

        VALUES (?, ?, ?, ?, ?, ?)
        """,

        (
            employee_id,
            employee_code,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            ip_address,
            device,
            status
        )
    )


def generate_temporary_pin():

    numbers = string.digits

    return "".join(
        random.choice(numbers)
        for _ in range(6)
    )


def reset_password_by_phone(phone):

    users = query(
        """
        SELECT *
        FROM employees
        WHERE phone=?
        AND status='Active'
        """,
        (phone.strip(),)
    )

    if users.empty:
        return None

    user = users.iloc[0]

    temporary_pin = generate_temporary_pin()

    execute(
        """
        UPDATE employees

        SET pin_hash=?,
            updated_at=?

        WHERE id=?
        """,

        (
            hash_pin(temporary_pin),
            datetime.now().isoformat(),
            int(user["id"])
        )
    )

    return {
        "employee_id": int(user["id"]),
        "employee_code": user["employee_code"],
        "temporary_pin": temporary_pin
    }


def change_pin(employee_id, new_pin):

    execute(
        """
        UPDATE employees

        SET pin_hash=?,
            updated_at=?

        WHERE id=?
        """,

        (
            hash_pin(new_pin),
            datetime.now().isoformat(),
            employee_id
        )
    )

    return True