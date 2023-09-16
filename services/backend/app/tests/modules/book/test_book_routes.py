from fastapi import status
import pytest
from httpx import AsyncClient
from datetime import datetime

from src.versions import ApiVersion
from src.modules.book.models import Book


model_class = Book
route_base = f"{ApiVersion.V1}/{model_class.__tablename__}"


@pytest.mark.anyio
async def test_get_all_empty(client: AsyncClient):
    response = await client.get(
        route_base
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data == []


@pytest.mark.anyio
async def test_create_one_with_all_fields(client: AsyncClient):
    response = await client.post(
        route_base,
        json={
            'identifier': '978-3-16-148410-0',
            'name': 'A Brief Horror Story of Time',
            'author': 'Stephen Hawk King',
            'release_year': 2035,
        }
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data['identifier'] == '978-3-16-148410-0'
    assert data['name'] == 'A Brief Horror Story of Time'
    assert data['author'] == 'Stephen Hawk King'
    assert data['release_year'] == 2035
    assert data['created_at'] is not None
    assert data['updated_at'] is not None


@pytest.mark.anyio
async def test_create_one_with_only_mandatory_fields(client: AsyncClient):
    response = await client.post(
        route_base,
        json={
            'identifier': '978-3-16-148410-1',
            'name': 'A Brief Horror Story of Time Part Deux',
            'author': 'Stephen Hawk King',
        }
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data['identifier'] == '978-3-16-148410-1'
    assert data['name'] == 'A Brief Horror Story of Time Part Deux'
    assert data['author'] == 'Stephen Hawk King'
    assert data['release_year'] is None
    assert data['created_at'] is not None
    assert data['updated_at'] is not None


@pytest.mark.anyio
async def test_update_one_with_all_fields(client: AsyncClient):
    item = await Book(
        **{
            'identifier': '978-3-16-148410-2',
            'name': 'A Brief Horror Story of Time Part Three',
            'author': 'Stephen Hawk Kingpin',
            'release_year': 2041,
        }
    ).save()

    response = await client.patch(
        f"/api/v1/book/{item.id}",
        json={
            'identifier': '978-3-16-148410-3',
            'name': 'A Brief Horror Story of Time Part 3',
            'author': 'Stephen Hawk Kingfisher',
            'release_year': 2039,
        }
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data['identifier'] == '978-3-16-148410-3'
    assert data['name'] == 'A Brief Horror Story of Time Part 3'
    assert data['author'] == 'Stephen Hawk Kingfisher'
    assert data['release_year'] == 2039
    assert datetime.fromisoformat(data['created_at']) == item.created_at
    assert datetime.fromisoformat(data['updated_at']) > item.updated_at
    assert datetime.fromisoformat(data['updated_at']) > datetime.fromisoformat(data['created_at'])


@pytest.mark.anyio
async def test_update_one_does_not_apply_none(client: AsyncClient):
    item = await Book(
        **{
            'identifier': '978-3-16-148410-88',
            'name': 'A Brief Horror Story of Time Part 89',
            'author': 'Stephen Hawk Kingpin',
            'release_year': 2041,
        }
    ).save()

    response = await client.patch(
        f"/api/v1/book/{item.id}",
        json={
            'identifier': '978-3-16-148410-89',
            'name': '',
            'author': None,
        }
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data['identifier'] == '978-3-16-148410-89'
    assert data['name'] == ''
    assert data['author'] == 'Stephen Hawk Kingpin'
    assert data['release_year'] == 2041
    assert datetime.fromisoformat(data['created_at']) == item.created_at
    assert datetime.fromisoformat(data['updated_at']) > item.updated_at
    assert datetime.fromisoformat(data['updated_at']) > datetime.fromisoformat(data['created_at'])


@pytest.mark.anyio
async def test_update_one_with_only_mandatory_fields(client: AsyncClient):
    item = await Book(
        **{
            'identifier': '978-3-16-148410-4',
            'name': 'A Brief Horror Story of Time Part Four',
            'author': 'Stephen Hawk Kingpin',
            'release_year': 2041,
        }
    ).save()
    response = await client.patch(
        f"/api/v1/book/{item.id}",
        json={
            'identifier': '978-3-16-148410-5',
            'name': 'A Brief Horror Story of Time Part 4',
            'author': 'Stephen Hawk Kingfisher',
        }
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data['identifier'] == '978-3-16-148410-5'
    assert data['name'] == 'A Brief Horror Story of Time Part 4'
    assert data['author'] == 'Stephen Hawk Kingfisher'
    assert data['release_year'] == 2041
    assert datetime.fromisoformat(data['created_at']) == item.created_at
    assert datetime.fromisoformat(data['updated_at']) > item.updated_at
    assert datetime.fromisoformat(data['updated_at']) > datetime.fromisoformat(data['created_at'])


@pytest.mark.anyio
async def test_update_one_with_payload_with_all_fields(client: AsyncClient):
    item = await Book(
        **{
            'identifier': '978-3-16-148410-8',
            'name': 'A Brief Horror Story of Time Part 8',
            'author': 'Stephen Hawk Kingpin',
            'release_year': 2041,
        }
    ).save()

    response = await client.patch(
        f"/api/v1/book/{item.id}",
        json={
            'id': item.id,
            'identifier': '978-3-16-148410-9',
            'name': 'A Brief Horror Story of Time: Payload Time',
            'author': 'Stephen Hawk Kingsmen Secret Service',
            'release_year': 2045,
        }
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data['identifier'] == '978-3-16-148410-9'
    assert data['name'] == 'A Brief Horror Story of Time: Payload Time'
    assert data['author'] == 'Stephen Hawk Kingsmen Secret Service'
    assert data['release_year'] == 2045
    assert datetime.fromisoformat(data['created_at']) == item.created_at
    assert datetime.fromisoformat(data['updated_at']) > item.updated_at
    assert datetime.fromisoformat(data['updated_at']) > datetime.fromisoformat(data['created_at'])


@pytest.mark.anyio
async def test_update_one_by_payload_with_only_mandatory_fields(client: AsyncClient):
    item = await Book(
        **{
            'identifier': '978-3-16-148410-12',
            'name': 'A Brief Horror Story of Time Part 11',
            'author': 'Stephen Hawk Kingpin',
            'release_year': 2041,
        }
    ).save()
    response = await client.patch(
        f"/api/v1/book/{item.id}",
        json={
            'id': item.id,
            'identifier': '978-3-16-148410-11',
            'name': 'A Brief Horror Story of Time Part Eleventy',
            'author': 'Stephen Hawk Kingklip',
        }
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data['identifier'] == '978-3-16-148410-11'
    assert data['name'] == 'A Brief Horror Story of Time Part Eleventy'
    assert data['author'] == 'Stephen Hawk Kingklip'
    assert data['release_year'] == 2041
    assert datetime.fromisoformat(data['created_at']) == item.created_at
    assert datetime.fromisoformat(data['updated_at']) > item.updated_at
    assert datetime.fromisoformat(data['updated_at']) > datetime.fromisoformat(data['created_at'])


@pytest.mark.anyio
async def test_delete_one(client: AsyncClient):
    item = await Book(
        **{
            'identifier': '978-3-16-148410-6',
            'name': 'A Brief Horror Story of Time Part 5',
            'author': 'Stephen Hawk Kingpin',
            'release_year': 2041,
        }
    ).save()
    item_count = await Book.get_count()
    response = await client.delete(
        f"/api/v1/book/{item.id}"
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data['message'] == f'Deleted one Book from the database.'
    assert data['count'] == 1
    assert (await Book.get_count()) == (item_count - 1)


@pytest.mark.anyio
async def test_create_bulk(client: AsyncClient):
    # Get count before
    item_count = await Book.get_count()

    # Create items
    response = await client.post(
        f"{route_base}/bulk",
        json=[
                # With all fields
                {
                    'identifier': '978-3-16-148410-15',
                    'name': 'A Brief Horror Story of Time 15',
                    'author': 'Stephen Hawk Kingston',
                    'release_year': 2039,
                },
                # With only mandatory fields
                {
                    'identifier': '978-3-16-148410-16',
                    'name': 'A Brief Horror Story of Time 16',
                    'author': 'Stephen Hawk Kingston Jamaica',
                }
        ]
    )

    # Assert response
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data['message'] == f'Created multiple Books in the database.'
    assert data['count'] == 2
    assert (await Book.get_count()) == (item_count + 2)

    # Assert values
    item1 = await Book.get_by_id(id=data['ids'][0])
    assert item1.identifier == '978-3-16-148410-15'
    assert item1.name == 'A Brief Horror Story of Time 15'
    assert item1.author == 'Stephen Hawk Kingston'
    assert item1.release_year == 2039
    assert item1.created_at is not None
    assert item1.updated_at is not None

    item2 = await Book.get_by_id(id=data['ids'][1])
    assert item2.identifier == '978-3-16-148410-16'
    assert item2.name == 'A Brief Horror Story of Time 16'
    assert item2.author == 'Stephen Hawk Kingston Jamaica'
    assert item2.release_year is None
    assert item2.created_at is not None
    assert item2.updated_at is not None


@pytest.mark.anyio
async def test_create_if_not_exists(client: AsyncClient):
    # Create items
    response = await client.put(
        route_base,
        json={
                'identifier': '978-3-16-148410-19',
                'name': 'A Brief Horror Story of Time 19',
                'author': 'Stephen Hawk Kingpinwheel',
                'release_year': 2022,
        }
    )

    # Assert response
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data['identifier'] == '978-3-16-148410-19'
    assert data['name'] == 'A Brief Horror Story of Time 19'
    assert data['author'] == 'Stephen Hawk Kingpinwheel'
    assert data['release_year'] == 2022
    assert data['created_at'] is not None
    assert data['updated_at'] is not None


@pytest.mark.anyio
async def test_update_if_exists(client: AsyncClient):
    # Create item
    item = await Book(
        **{
            'identifier': '978-3-16-148410-21',
            'name': 'A Brief Horror Story of Time 20',
            'author': 'Stephen Hawk Kingmaker',
            'release_year': 2022,
        }
    ).save()

    # Update item
    response = await client.put(
        route_base,
        json={
                'identifier': '978-3-16-148410-21',
                'name': 'A Brief Horror Story of Time 21',
                'author': 'Stephen Hawk Kingmakers Mark',
                'release_year': 2023,
        }
    )

    # Assert response
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data['identifier'] == '978-3-16-148410-21'
    assert data['name'] == 'A Brief Horror Story of Time 21'
    assert data['author'] == 'Stephen Hawk Kingmakers Mark'
    assert data['release_year'] == 2023
    assert data['created_at'] is not None
    assert data['updated_at'] is not None


@pytest.mark.anyio
async def test_create_or_update_bulk(client: AsyncClient):
    # Get count before
    item_count = await Book.get_count()

    # Create items
    response = await client.put(
        f"{route_base}/bulk",
        json=[
                # With all fields
                {
                    'identifier': '978-3-16-148410-35',
                    'name': 'A Brief Horror Story of Time 31',
                    'author': 'Stephen Hawk Kingstongue',
                    'release_year': 2039,
                },
                # With only mandatory fields
                {
                    'identifier': '978-3-16-148410-36',
                    'name': 'A Brief Horror Story of Time 35',
                    'author': 'Stephen Hawk Kingstonic',
                }
        ]
    )

    # Assert response
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data['message'] == f'Created or updated multiple Books in the database.'
    assert data['count'] == 2
    assert (await Book.get_count()) == (item_count + 2)

    # Assert values
    item1 = await Book.get_by_id(id=data['ids'][0])
    assert item1.identifier == '978-3-16-148410-35'
    assert item1.name == 'A Brief Horror Story of Time 31'
    assert item1.author == 'Stephen Hawk Kingstongue'
    assert item1.release_year == 2039
    assert item1.created_at is not None
    assert item1.updated_at is not None

    item2 = await Book.get_by_id(id=data['ids'][1])
    assert item2.identifier == '978-3-16-148410-36'
    assert item2.name == 'A Brief Horror Story of Time 35'
    assert item2.author == 'Stephen Hawk Kingstonic'
    assert item2.release_year is None
    assert item2.created_at is not None
    assert item2.updated_at is not None

    item_count_pre_update = await Book.get_count()

    # Update items
    response = await client.put(
        f"{route_base}/bulk",
        json=[
                # With all fields
                {
                    'identifier': '978-3-16-148410-35',
                    'name': 'A Brief Horror Story of Time 35',
                    'author': 'Stephen Hawk Kingstongues',
                    'release_year': 2049,
                },
                # With only mandatory fields
                {
                    'identifier': '978-3-16-148410-36',
                    'name': 'A Brief Horror Story of Time 36',
                    'author': 'Stephen Hawk Kingstonic And Gin',
                }
        ]
    )

    # Assert response
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data['message'] == f'Created or updated multiple Books in the database.'
    assert data['count'] == 2
    assert (await Book.get_count()) == item_count_pre_update

    # Assert values
    item3 = await Book.get_by_id(id=data['ids'][0])
    assert item3.id == item1.id
    assert item3.identifier == '978-3-16-148410-35'
    assert item3.name == 'A Brief Horror Story of Time 35'
    assert item3.author == 'Stephen Hawk Kingstongues'
    assert item3.release_year == 2049
    assert item3.created_at is not None
    assert item3.updated_at is not None

    item4 = await Book.get_by_id(id=data['ids'][1])
    assert item4.id == item2.id
    assert item4.identifier == '978-3-16-148410-36'
    assert item4.name == 'A Brief Horror Story of Time 36'
    assert item4.author == 'Stephen Hawk Kingstonic And Gin'
    assert item4.release_year is None
    assert item4.created_at is not None
    assert item4.updated_at is not None


@pytest.mark.anyio
async def test_get_all_full(client: AsyncClient):
    # Get from route
    response = await client.get(
        route_base
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    all_books_route = response.json()
    # all_books_route.sort(key='id')

    # Get directly from db
    all_books_db = await Book.fetch_all()
    # all_books_db.sort(key='id')

    # assert len(all_books_route) == len(all_books_db)
