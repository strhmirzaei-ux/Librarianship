from typing import Annotated

from fastapi import FastAPI, HTTPException, Path, Response, status
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(
    title="BookShelf API",
    description="A small in-memory library API built with FastAPI.",
    version="1.0.0",
)


class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=120)
    year: int | None = Field(default=None, ge=0, le=9999)
    isbn: str | None = Field(default=None, max_length=20)


class BookUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=200)
    author: str | None = Field(default=None, min_length=1, max_length=120)
    year: int | None = Field(default=None, ge=0, le=9999)
    isbn: str | None = Field(default=None, max_length=20)


class Book(BookCreate):
    id: int


books: dict[int, Book] = {}
next_book_id = 1


@app.get("/books", response_model=list[Book], tags=["books"])
def list_books() -> list[Book]:
    return list(books.values())


@app.post("/books", response_model=Book, status_code=status.HTTP_201_CREATED, tags=["books"])
def create_book(book_data: BookCreate) -> Book:
    global next_book_id
    book = Book(id=next_book_id, **book_data.model_dump())
    books[next_book_id] = book
    next_book_id += 1
    return book


@app.get("/books/{book_id}", response_model=Book, tags=["books"])
def get_book(book_id: Annotated[int, Path(gt=0)]) -> Book:
    book = books.get(book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book


@app.patch("/books/{book_id}", response_model=Book, tags=["books"])
def update_book(book_id: Annotated[int, Path(gt=0)], changes: BookUpdate) -> Book:
    book = books.get(book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    updated_fields = changes.model_dump(exclude_unset=True)
    if any(value is None for value in updated_fields.values()):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Book fields cannot be set to null")

    updated_book = book.model_copy(update=updated_fields)
    books[book_id] = updated_book
    return updated_book


@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["books"])
def delete_book(book_id: Annotated[int, Path(gt=0)]) -> Response:
    if books.pop(book_id, None) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
