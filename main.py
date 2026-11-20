from collections import UserDict
from datetime import datetime, timedelta
import calendar
import pickle


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __str__(self):
        return str(self.value)


# NEW
class Birthday(Field):
    def __init__(self, value):
        try:
            birth_date = datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        super().__init__(birth_date)

    def __str__(self):
        return self.value.strftime("%d.%m.%Y")


class Phone(Field):
    def __init__(self, value):
        if not value.isdigit() or len(value) != 10:
            raise ValueError("phone has to be 10 digit characters long")
        super().__init__(value)

    # redefining equals to be able to use ==
    def __eq__(self, another_phone):
        return isinstance(another_phone, Phone) and self.value == another_phone.value

    def __str__(self):
        return str(self.value)


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    # adds a phone after checking if the phone already exists
    def add_phone(self, phone: str):
        new_phone = Phone(phone)
        if new_phone in self.phones:
            raise ValueError(f"The phone is already associated with {self.name}")
        
        self.phones.append(new_phone)
          

    def remove_phone(self, phone: str):
        target_phone = Phone(phone)
        if target_phone not in self.phones:
            raise ValueError(f"{phone} isn't associated with {self.name}")
        self.phones.remove(target_phone)
        

    def edit_phone(self, old_phone: str, new_phone: str):
        # will fall if new phone doesn't meet the validation rules
        old = Phone(old_phone)
        new = Phone(new_phone)
        if old not in self.phones:
            raise ValueError(f"{old_phone} not found")
        if new in self.phones and new != old:
            raise ValueError(f"Phone {new_phone} already exists")
        self.phones[self.phones.index(old)] = new


    def find_phone(self, phone: str):
        return (
            self.phones[self.phones.index(Phone(phone))]
            if Phone(phone) in self.phones
            else None
        )

    def __str__(self):
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}"

    # NEW
    def add_birthday(self, birthday):
        birth_date = Birthday(birthday)
        if birth_date.value > datetime.today():
            raise ValueError("Birthday date cannot be in the future")
        self.birthday = birth_date


class AddressBook(UserDict):

    def add_record(self, record: Record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if self.data.get(name) is not None:
            self.data.pop(name)
        else:
            raise ValueError(f"Contact {name} not found")

    def is_empty(self):
        return True if self.data == {} else False

    # NEW
    # returns list of dict of users that should be congratulated with bd within upcoming week
    def get_upcoming_birthdays(self):

        today = datetime.today()
        bd_date = None
        days = 7

        user_birth_date = None
        upcoming_birthdays = []

        for record in self.data.values():
            if record.birthday is None:
                continue
            user_birth_date = record.birthday.value.date()

            if (
                user_birth_date.month == 2
                and user_birth_date.day == 29
                and not calendar.isleap(today.year)
            ):
                #  user_birth_date.day = 28
                user_birth_date = user_birth_date.replace(day=28)

            # get possible dates of birthdays for the week to then check if it matches the bd date of the user
            for i in range(days):
                bd_date = today + timedelta(days=i)
                if (
                    bd_date.month == user_birth_date.month
                    and bd_date.day == user_birth_date.day
                ):
                    congratulation_date = AddressBook.shift_from_weekend(bd_date)
                    upcoming_birthdays.append(
                        {
                            "name": record.name.value,
                            "congratulation_date": congratulation_date.strftime(
                                "%Y.%m.%d"
                            ),
                        }
                    )

        return upcoming_birthdays

    # shifts congratulation day to Monday if it is on Saturday or Sunday
    @staticmethod
    def shift_from_weekend(day):
        if day.weekday() == 5:
            return day + timedelta(days=2)
        if day.weekday() == 6:
            return day + timedelta(days=1)
        return day


# decorator function
def input_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return str(e)
        except KeyError as e:
            return str(e)

    #  except Exception:
    #      return "Something went wrong"
    return wrapper


# functions layer between the user and the classes
@input_error
def add_contact(args, book):
    if len(args) < 2:
        raise ValueError("Correct format: add [Contact name] [phone number]")

    name, phone, *_ = args
    record = book.find(name)

    if record is None:
        record = Record(name)
        record.add_phone(phone)
        book.add_record(record)
        return "Contact added"
    
    record.add_phone(phone)
    return "Contact updated"


@input_error
def delete_contact(args, book):
    if len(args) < 1:
        raise ValueError("Correct format: delete [Contact name]")
    
    name, *_ = args
    book.delete(name)
    return "Contact deleted"



@input_error
def change_contact(args, book):
    if len(args) < 3:
        raise ValueError("Correct format: change [Contact name] [Old phone] [Newphone]")

    name, old_phone, new_phone, *_ = args
    record = book.find(name)

    if record is None:
        raise ValueError("No such contact")

    record.edit_phone(old_phone, new_phone)
    return "Contact updated"


@input_error
def show_phone(args, book):
    if len(args) != 1:
        raise ValueError("Correct format: phone [Contact name]")

    name, *_ = args
    record = book.find(name)

    if record is None:
        raise ValueError("Contact not found")

    return f"{record.name} {', '.join(str(phone) for phone in record.phones)}"


@input_error
def show_all_contacts(args, book: AddressBook):
    if book.is_empty():
        return "Contact book is empty"
    result = ""
    for record in book.data.values():
        result += f"{record.name} {', '.join(str(phone) for phone in record.phones)}\n"
    return result


@input_error
def add_birthday(args, book: AddressBook):
    if len(args) < 2:
        raise ValueError("Correct format:  add-birthday [Contact name] DD.MM.YYYY in digits")
    name, birthday, *_ = args
    record = book.find(name)
    if record is None:
        return "No such contact"

    record.add_birthday(birthday)
    return "Birth date added"


@input_error
def show_birthday(args, book):
    if len(args) != 1:
        raise ValueError("Correct format: show-birthday [Contact name] ")
    name, *_ = args
    record = book.find(name)
    if record is None:
        return "No such contact"

    if record.birthday is None:
        return "No information"
    return f"{name} celebrates birthday on {record.birthday}"


@input_error
def show_upcoming_birthdays(args, book: AddressBook):
    if book.is_empty():
        return "Contact book is empty"

    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No birthdays next week"
    result = ""
    for user in upcoming:
        result += f"{user['name']}: {user['congratulation_date']}\n"
    return result


def parse_input(user_input):

    command, *args = user_input.split()
    command = command.strip().lower()
    return command, *args


def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()  # Повернення нової адресної книги, якщо файл не знайдено

def main():
    book = load_data()
    print("Welcome to the assistant bot!")
    try:

        while True:
            user_input = input("Enter a command: ")
            if not user_input.strip():
                continue
            command, *args = parse_input(user_input)

            if command in ["close", "exit"]:
                save_data(book)
                print("Good bye!")
                break

            elif command == "hello":
                print("How can I help you?")

            elif command == "add":
                print(add_contact(args, book))

            elif command == "change":
                print(change_contact(args, book))

            elif command == "phone":
                print(show_phone(args, book))

            elif command == "all":
                print(show_all_contacts(args, book))

            elif command == "add-birthday":
                print(add_birthday(args, book))

            elif command == "show-birthday":
                print(show_birthday(args, book))

            elif command == "birthdays":
                print(show_upcoming_birthdays(args, book))

            elif command == "delete":
                print(delete_contact(args,book))

            else:
                print("Invalid command.")
    finally:
        save_data(book)


if __name__ == "__main__":
    main()