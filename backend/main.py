import inspect
import logging
import os
import sys
from re import match

import pandas as pd

# csv file path
COLLECTION_PATH = "collection.csv"

# logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(message)s",
    filename="log.log",
)


class Wallet:
    """Wallet with a bunch of methods to manage it."""

    def __init__(self, filename):
        # wallet category types
        self.CATEGORIES = ("Доход", "Расход")

        # wallet date format
        self.DATE_PATTERN = r"\d{4}-\d{2}-\d{2}"

        # wallet columns
        self.COLUMNS = ("date", "category", "amount", "description")

        # functions to change balance
        self.BALANCE_CHANGERS: dict = {
            "Доход": self.increase_balance,
            "Расход": self.decrease_balance,
        }

        # max length of description
        self.MAX_DESC_LENGTH = 64

        self.filename = filename
        self.data = self.__load_data()
        self.__set_balance()

    def __load_data(self):
        """Returns the data from the csv file or generate a new one."""
        if os.path.exists(self.filename):
            return pd.read_csv(self.filename, index_col=0)  # reading from the csv file
        else:
            return pd.DataFrame(columns=self.COLUMNS)  # generating a new one DataFrame

    def get_balance(self) -> float:
        """Returns current balance."""
        return self.balance

    def __set_balance(self) -> None:
        """Init for the base balance."""
        income = self.data[self.data["category"] == "Доход"]["amount"].sum()
        expenses = self.data[self.data["category"] == "Расход"]["amount"].sum()
        self.balance = income - expenses

    def __save_data(self):
        """Save data to the file."""
        self.data.to_csv(self.filename, index_label="id")

    def __change_amount(self, prev_category, index, amount: float) -> bool:
        """
        Returns bool type value, as it checks whether
        the amount can be changed or not.

          prev_category
           Previous category of the DataFrame row.
          index
           Identifier of the DataFrame row.
          amount
           Current amount of the DataFrame row.
        """
        category = self.data.loc[index, "category"]
        prev_amount = self.data.loc[index, "amount"] * pow(
            -1, 1 if prev_category == category else 0
        )  # getting the previous value of amount to get a fake balance
        if (
            fake_balance := self.balance - prev_amount - amount
            if category == "Расход"
            else self.balance + prev_amount + amount
        ) >= 0:
            self.balance = fake_balance
            return True
        return False

    def __change_category(
        self, category: str, index: int, amount: float = None
    ) -> bool:
        """
        Returns bool type value, as it checks whether
        the category can be changed or not.

          category
           Inspected category.
          index
           Identifier of the DataFrame row.
          amount
           Column of the DataFrame row
        """
        prev_amount = self.data.loc[index, "amount"]
        curr_amount = amount if amount else prev_amount
        if (
            fake_balance := self.balance - prev_amount - curr_amount
            if category == "Расход"
            else self.balance + prev_amount + curr_amount
        ) >= 0:
            if not amount:
                self.balance = fake_balance
            return True
        return False

    def increase_balance(self, amount) -> bool:
        """Increase the wallet balance."""
        self.balance += amount
        return True

    def decrease_balance(self, amount) -> bool:
        """
        Check whether the new balance is positive
        and decrease the wallet balance.
        """

        if (fake_balance := self.balance - amount) >= 0:
            self.balance: float = fake_balance
            return True  # True if the new balance is positive
        print(
            "На Вашем кошельке недостаточно средств, "
            "чтобы снять такую сумму, пожалуйста, попробуйте заново!\n"
        )
        return False

    def add_entry(
        self,
        category: str = None,
        date: str = None,
        amount: float = None,
        description: str = None,
    ):
        """Add a new DataFrame row and save it to a file."""
        try:
            if (
                category
                and description and len(description) < self.MAX_DESC_LENGTH
                and self.BALANCE_CHANGERS.get(category)(amount)
            ):
                new_entry = {  # future DataFrame row
                    "date": [pd.to_datetime(date, format="%Y-%m-%d")]
                    if date is not None and match(self.DATE_PATTERN, date)
                    else pd.Timestamp.now().date(),
                    "category": [category],
                    "amount": [amount],
                    "description": [description],
                }
                self.data = pd.concat(
                    [self.data, pd.DataFrame(new_entry)], ignore_index=True
                ) if len(self.data) else pd.DataFrame(new_entry)
                self.__save_data()  # save data to the file
                return
            print("Проверьте корректность введенных данных!")
        except TypeError as e:
            print("Вы не заполнили обязательные поля! Пожалуйста, попробуйте заново.\n")
            logging.warning(e)

    def edit_entry(
        self,
        index: int,
        category: str = None,
        date=None,
        amount: float = None,
        description: str = None,
    ) -> None:
        """
        Edit an existing DataFrame row and save it to a file.

          index
           Identifier of the existing DataFrame row.
          category, date, amount, description
           Just columns of the DataFrame row.

        """
        try:
            _ = self.data.loc[
                [
                    index,
                ]
            ]
            prev_category = self.data.loc[index, "category"]
            if (
                category
                and category in self.CATEGORIES
                and category != self.data.loc[index, "category"]
            ):
                if self.__change_category(category, index, amount):
                    self.data.loc[index, "category"] = category
            if date and match(self.DATE_PATTERN, date):
                self.data.loc[index, "date"] = pd.to_datetime(date, format="%Y-%m-%d")
            if amount and self.__change_amount(prev_category, index, amount):
                self.data.loc[index, "amount"] = amount
            if description and len(description) < self.MAX_DESC_LENGTH:
                self.data.loc[index, "description"] = description
            self.__save_data()  # save data to the file
        except KeyError as e:
            print("Номер записи некорректен, пожалуйста, попробуйте заново!\n")
            logging.warning(e)

    def search_entries(
        self, index: int = None, category: str = None, date=None, amount: float = None
    ):
        """
        Returns objects that match the search criteria.

          index
           Identifier of the searched DataFrame row.
          category
           Searching by category (Доход/Расход).
          date
           Searching by date (Y-m-d).
          amount
           Searching by amount.
        """
        try:
            if index or index == 0:
                return self.data.loc[
                    [
                        index,
                    ]
                ]
            if category:
                return self.data[self.data["category"] == category]
            if date:
                return self.data[self.data["date"] == date]
            if amount:
                return self.data[self.data["amount"] == amount]
        except (KeyError, ValueError) as e:
            print(
                "Пожалуйста, проверьте данные, которые Вы ввели и попробуйте заново!\n"
            )
            logging.warning(e)


class Menu:
    """Menu with own options and loop of selecting them."""

    def __init__(self, title):
        self.title = title
        self.options = []

    def add_option(self, label, action, args=None) -> None:
        """Add a new option to the menu."""
        if args is None:
            args = []
        self.options.append((label, action, args))

    def option(self, number: int) -> None:
        """
        Returns the result of executing the function passed by the action
        parameter. The number corresponds to the parameters of function
        which will be obtained using options of object.
        """
        try:
            option = self.options[number]  # getting current option
            argcount: int = len(inspect.signature(option[1]).parameters)
            action = self.options[number][1]
            params = self.options[number][2].copy()
            if params and sum(1 for el in params if el is None) != argcount:
                for el in range(argcount):
                    for param, to_type in params[el].items():
                        value = input(f'Введите параметр "{param}": ')
                        params[el] = to_type(value) if value else None
            return action(*params)
        except ValueError as e:
            print("Пожалуйста, проверьте данные, которые Вы ввели и попробуйте заново!")
            logging.warning(e)

    def show(self):
        """Shows the options of menu."""
        for el in enumerate(self.options):
            print(f"{el[0] + 1}. {el[1][0]}")

    def start(self) -> None:
        """Starts an infinite loop of selecting menu items."""
        while True:
            try:
                self.show()
                choice = int(input("Пожалуйста, выберите пункт меню: ")) - 1
                if (res := self.option(choice)) is not None:
                    print(f"{res}\n")
            except (IndexError, ValueError) as e:
                print("\nПожалуйста, выберите корректный пункт меню!\n")
                logging.warning(e)


# wallet setup
wallet = Wallet(COLLECTION_PATH)

# menu setup
menu = Menu("Wallet Menu")
menu.add_option(label="Вывести баланс", action=wallet.get_balance)
menu.add_option(
    label="Редактировать запись",
    action=wallet.edit_entry,
    args=[
        {"номер": int},
        {"категория (Доход/Расход)": str},
        {"дата (Y-m-d)": str},
        {"сумма": float},
        {"описание": str},
    ],
)
menu.add_option(
    label="Поиск записей по полю",
    action=wallet.search_entries,
    args=[
        {"номер": int},
        {"категория (Доход, Расход)": str},
        {"дата": str},
        {"сумма": float},
    ],
)
menu.add_option(
    label="Добавить новую запись",
    action=wallet.add_entry,
    args=[
        {"категория (Доход, Расход)": str},
        {"дата (Y-m-d)": str},
        {"сумма": float},
        {"описание": str},
    ],
)
menu.add_option(label="Выйти", action=sys.exit)
