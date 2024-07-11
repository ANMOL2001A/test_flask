"""
Purpose: Create helper functions
Module: api
Author: Anmol Sharma
Copyright (C) Cynoteck Software Solutions - 2024
"""
from pydantic import BaseModel, field_validator
import json
import re
from flask import request



error_messages = {
    "310": "Message is not in proper format. Please check your text again.",
    "404": "User not found",
    "500": "Failed to generate a response due to an internal error.",
    "400": "Bad request, no file part in the request",
    "501": "Uploaded File Already exists",
    "502": "Dataset directory does not exist.",
    "503": "Failed to reset dataset",
    "504": "Only Markdown files (.md) are allowed.",
    "100": "Message cannot be empty.",
    "101": "Queries should not consist solely of numeric values. Please revise the query and resend. Thank you for your cooperation!",
    "102": "Message cannot be '_' followed by underscores.",
    "103": "Your message exceeds the 350-character limit. Please shorten your query and resend. We appreciate your cooperation. Thank you!",
    "104": "Your message contains a special character ({}) which isn't allowed. Please remove it and resend your query. Thank you for your understanding.",
    "107": "Kindly ensure there are no white spaces in your query. Please revise and resend. We appreciate your cooperation."
}


class CustomValidationError(Exception):
    def __init__(self, message: str, error_code: int):
        super().__init__(message)
        self.error_code = error_code


class MessageInput(BaseModel):
    """
    Represents the input data for submitting a message.
    """
    message: str
    phone_number: str

    @field_validator("message")
    def validate_message(cls, value):
        if not value:
            raise CustomValidationError(error_messages["100"], 100)
        if value.isdigit():
            raise CustomValidationError(error_messages["101"], 101)
        if len(value) > 350:
            raise CustomValidationError(error_messages["103"], 103)
        if not re.match(r"^[a-zA-Z0-9\s.,!?;'\"\[\]%&*|\\/`–—_-]*$", value):
            invalid_characters = re.findall(r"[^\w\s.,!?;'\"\[\]%&*|\\/`–—_-]", value)
            invalid_characters_str = ", ".join(invalid_characters)
            error_message = error_messages["104"].format(invalid_characters_str)
            raise CustomValidationError(error_message, 104)
        if re.match(r"^\s*$", value):
            raise CustomValidationError(error_messages["107"], 107)
        return value


class UploadInput(BaseModel):
    file: bytes

    @staticmethod
    def validate_file_extension(filename: str):
        if not filename.lower().endswith('.md'):
            raise ValueError("Only Markdown files (.md) are allowed.")

    @field_validator('file', mode='before')
    def check_file_extension(cls, value):
        filename = request.files['file'].filename
        cls.validate_file_extension(filename)
        return value
