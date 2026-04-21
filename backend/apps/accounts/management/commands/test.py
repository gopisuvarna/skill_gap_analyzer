"""Custom test command to run Django's native test runner."""
from django.core.management.base import BaseCommand
from django.core.management.commands.test import Command as TestCommand


class Command(TestCommand, BaseCommand):
    pass