"""
Database Operations Tests

These tests verify database operations on real tables after migrations run.
They use Config.DATABASE_URL from environment variables.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from sqlmodel import select, delete
from sqlmodel.ext.asyncio.session import AsyncSession

from src.app.models.user import User, UserRole
from src.app.models.client import Client
from src.app.models.client_document import ClientDocument
from src.app.models.property import Property
from src.app.models.conversation_session import ConversationSession
from src.app.models.transcript import Transcript
from src.app.models.escalation import Escalation
from src.app.utils.utils import generate_hash_password
from config import Config


class TestDatabaseConnection:
    """Test database connection and basic operations"""
    
    @pytest.mark.asyncio
    async def test_database_url_from_env(self):
        """Verify DATABASE_URL is loaded from environment"""
        assert Config.DATABASE_URL is not None
        assert "postgresql" in Config.DATABASE_URL or "postgres" in Config.DATABASE_URL
        print(f"\n✓ Using database: {Config.DATABASE_URL.replace(Config.DATABASE_URL.split('@')[0], '***')}")


class TestUserOperations:
    """Test User table CRUD operations"""
    
    @pytest.mark.asyncio
    async def test_create_user(self, db_session: AsyncSession):
        """Create a user and verify it's in the database"""
        user = User(
            name="Test User",
            email="test_user@example.com",
            password_hash=generate_hash_password("password123"),
            role=UserRole.OWNER,
            firstname="Test",
            lastname="User",
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == "test_user@example.com"
        print(f"\n✓ Created user with ID: {user.id}")
    
    @pytest.mark.asyncio
    async def test_read_user(self, db_session: AsyncSession):
        """Create and then read a user from database"""
        # Create
        user = User(
            name="Read Test User",
            email="read_test@example.com",
            password_hash=generate_hash_password("password123"),
            role=UserRole.AGENT,
            firstname="Read",
            lastname="Test"
        )
        db_session.add(user)
        await db_session.commit()
        
        # Read back
        result = await db_session.execute(
            select(User).where(User.email == "read_test@example.com")
        )
        fetched_user = result.scalar_one()
        
        assert fetched_user.name == "Read Test User"
        assert fetched_user.role == UserRole.AGENT
        print(f"\n✓ Read user: {fetched_user.name} ({fetched_user.email})")
    
    @pytest.mark.asyncio
    async def test_update_user(self, db_session: AsyncSession):
        """Update a user and verify changes"""
        # Create
        user = User(
            name="Update Test",
            email="update_test@example.com",
            password_hash=generate_hash_password("password123"),
            role=UserRole.OWNER,
            firstname="Update",
            lastname="Test"
        )
        db_session.add(user)
        await db_session.commit()
        
        # Update
        user.name = "Updated Name"
        user.firstname = "Updated"
        await db_session.commit()
        await db_session.refresh(user)
        
        # Verify
        result = await db_session.execute(
            select(User).where(User.id == user.id)
        )
        updated = result.scalar_one()
        assert updated.name == "Updated Name"
        print(f"\n✓ Updated user name to: {updated.name}")
    
    @pytest.mark.asyncio
    async def test_delete_user(self, db_session: AsyncSession):
        """Delete a user and verify it's removed"""
        # Create
        user = User(
            name="Delete Test",
            email="delete_test@example.com",
            password_hash=generate_hash_password("password123"),
            role=UserRole.OWNER,
            firstname="Delete",
            lastname="Test"
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        user_id = user.id
        
        # Delete
        await db_session.delete(user)
        await db_session.commit()
        
        # Verify
        result = await db_session.execute(
            select(User).where(User.id == user_id)
        )
        assert result.scalar_one_or_none() is None
        print(f"\n✓ Deleted user with ID: {user_id}")
    
    @pytest.mark.asyncio
    async def test_list_all_users(self, db_session: AsyncSession):
        """Create multiple users and list them"""
        # Create multiple users
        users = [
            User(name=f"List User {i}", email=f"list{i}@example.com", 
                 password_hash=generate_hash_password("pass"), role=UserRole.OWNER,
                 firstname="List", lastname=f"User{i}")
            for i in range(3)
        ]
        for user in users:
            db_session.add(user)
        await db_session.commit()
        
        # List all
        result = await db_session.execute(select(User))
        all_users = result.scalars().all()
        
        assert len(all_users) >= 3
        print(f"\n✓ Listed {len(all_users)} users in database")


class TestClientOperations:
    """Test Client table operations"""
    
    @pytest.mark.asyncio
    async def test_create_client(self, db_session: AsyncSession, owner_user: User):
        """Create a client and verify"""
        client = Client(
            phone="+1234567890",
            name="Test Client",
            email="client@example.com",
            user_id=owner_user.id,
            is_onboarded=False
        )
        db_session.add(client)
        await db_session.commit()
        await db_session.refresh(client)
        
        assert client.id is not None
        assert client.phone == "+1234567890"
        print(f"\n✓ Created client with ID: {client.id}")
    
    @pytest.mark.asyncio
    async def test_update_client_onboarding(self, db_session: AsyncSession, owner_user: User):
        """Update client onboarding status"""
        client = Client(
            phone="+1987654321",
            name="Onboarding Test",
            user_id=owner_user.id,
            is_onboarded=False
        )
        db_session.add(client)
        await db_session.commit()
        
        # Update onboarding
        client.is_onboarded = True
        client.onboarding_data = {"budget": 500000, "location": "Miami"}
        await db_session.commit()
        
        # Verify
        result = await db_session.execute(
            select(Client).where(Client.phone == "+1987654321")
        )
        updated = result.scalar_one()
        assert updated.is_onboarded is True
        assert "budget" in updated.onboarding_data
        print(f"\n✓ Updated client onboarding: {updated.onboarding_data}")
    
    @pytest.mark.asyncio
    async def test_client_with_preferences(self, db_session: AsyncSession, owner_user: User):
        """Create client with preferences"""
        client = Client(
            phone="+15550001111",
            name="Preferences Client",
            user_id=owner_user.id,
            preferences={
                "property_type": "house",
                "bedrooms": 3,
                "bathrooms": 2,
                "budget_max": 600000
            }
        )
        db_session.add(client)
        await db_session.commit()
        await db_session.refresh(client)
        
        assert client.preferences is not None
        assert client.preferences.get("property_type") == "house"
        print(f"\n✓ Created client with preferences: {client.preferences}")


class TestPropertyOperations:
    """Test Property table operations"""
    
    @pytest.mark.asyncio
    async def test_create_property(self, db_session: AsyncSession, owner_user: User):
        """Create a property listing"""
        property = Property(
            title="Test Property",
            description="A beautiful test property",
            price=500000,
            bedrooms=3,
            bathrooms=2,
            location="Miami, FL",
            square_feet=2000,
            user_id=owner_user.id,
            is_active=True
        )
        db_session.add(property)
        await db_session.commit()
        await db_session.refresh(property)
        
        assert property.id is not None
        assert property.price == 500000
        print(f"\n✓ Created property: {property.title} (${property.price:,})")
    
    @pytest.mark.asyncio
    async def test_search_properties_by_location(self, db_session: AsyncSession, owner_user: User):
        """Create and search properties by location"""
        # Create properties in different locations
        properties = [
            Property(title="Miami House", location="Miami, FL", price=500000,
                    bedrooms=3, bathrooms=2, user_id=owner_user.id),
            Property(title="LA Condo", location="Los Angeles, CA", price=700000,
                    bedrooms=2, bathrooms=2, user_id=owner_user.id),
            Property(title="Miami Condo", location="Miami Beach, FL", price=600000,
                    bedrooms=2, bathrooms=1, user_id=owner_user.id)
        ]
        for prop in properties:
            db_session.add(prop)
        await db_session.commit()
        
        # Search Miami properties
        result = await db_session.execute(
            select(Property).where(Property.location.contains("Miami"))
        )
        miami_props = result.scalars().all()
        
        assert len(miami_props) >= 2
        print(f"\n✓ Found {len(miami_props)} properties in Miami")
    
    @pytest.mark.asyncio
    async def test_property_filters(self, db_session: AsyncSession, owner_user: User):
        """Test filtering properties by various criteria"""
        # Create properties with different criteria
        properties = [
            Property(title="Budget House", price=300000, bedrooms=2, 
                    bathrooms=1, location="Test City", user_id=owner_user.id),
            Property(title="Luxury House", price=900000, bedrooms=4,
                    bathrooms=3, location="Test City", user_id=owner_user.id),
            Property(title="Mid Range", price=500000, bedrooms=3,
                    bathrooms=2, location="Test City", user_id=owner_user.id)
        ]
        for prop in properties:
            db_session.add(prop)
        await db_session.commit()
        
        # Filter by price range
        result = await db_session.execute(
            select(Property).where(
                Property.price >= 400000,
                Property.price <= 600000
            )
        )
        filtered = result.scalars().all()
        
        assert len(filtered) >= 1
        print(f"\n✓ Found {len(filtered)} properties in $400k-$600k range")


class TestConversationOperations:
    """Test Conversation and Transcript operations"""
    
    @pytest.mark.asyncio
    async def test_create_conversation_session(self, db_session: AsyncSession, owner_user: User):
        """Create a conversation session"""
        session = ConversationSession(
            phone="+1234567890",
            user_id=owner_user.id,
            session_started=datetime.now(timezone.utc),
            is_active=True
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)
        
        assert session.id is not None
        assert session.phone == "+1234567890"
        print(f"\n✓ Created conversation session: {session.id}")
    
    @pytest.mark.asyncio
    async def test_add_transcripts(self, db_session: AsyncSession, owner_user: User):
        """Add transcripts to a conversation"""
        # Create session
        session = ConversationSession(
            phone="+15551234567",
            user_id=owner_user.id,
            session_started=datetime.now(timezone.utc),
            is_active=True
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)
        
        # Add transcripts
        transcripts = [
            Transcript(
                session_id=session.id,
                message="Hello, I'm looking for a house",
                sender="user",
                timestamp=datetime.now(timezone.utc)
            ),
            Transcript(
                session_id=session.id,
                message="I'd be happy to help you find a house!",
                sender="agent",
                timestamp=datetime.now(timezone.utc)
            )
        ]
        for t in transcripts:
            db_session.add(t)
        await db_session.commit()
        
        # Verify transcripts
        result = await db_session.execute(
            select(Transcript).where(Transcript.session_id == session.id)
        )
        saved_transcripts = result.scalars().all()
        
        assert len(saved_transcripts) == 2
        print(f"\n✓ Added {len(saved_transcripts)} transcripts to session")
    
    @pytest.mark.asyncio
    async def test_list_session_transcripts(self, db_session: AsyncSession, owner_user: User):
        """List all transcripts for a session"""
        # Create session with transcripts
        session = ConversationSession(
            phone="+17778889999",
            user_id=owner_user.id,
            session_started=datetime.now(timezone.utc)
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)
        
        # Add multiple messages
        for i in range(5):
            transcript = Transcript(
                session_id=session.id,
                message=f"Message {i}",
                sender="user" if i % 2 == 0 else "agent",
                timestamp=datetime.now(timezone.utc)
            )
            db_session.add(transcript)
        await db_session.commit()
        
        # List transcripts ordered by timestamp
        result = await db_session.execute(
            select(Transcript)
            .where(Transcript.session_id == session.id)
            .order_by(Transcript.timestamp)
        )
        transcripts = result.scalars().all()
        
        assert len(transcripts) == 5
        print(f"\n✓ Listed {len(transcripts)} transcripts for session")


class TestEscalationOperations:
    """Test Escalation operations"""
    
    @pytest.mark.asyncio
    async def test_create_escalation(self, db_session: AsyncSession, owner_user: User, agent_user: User):
        """Create an escalation request"""
        escalation = Escalation(
            client_phone="+1234567890",
            user_id=owner_user.id,
            agent_id=agent_user.id,
            reason="Client requested human agent",
            status="pending",
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(escalation)
        await db_session.commit()
        await db_session.refresh(escalation)
        
        assert escalation.id is not None
        assert escalation.status == "pending"
        print(f"\n✓ Created escalation: {escalation.id} ({escalation.reason})")
    
    @pytest.mark.asyncio
    async def test_update_escalation_status(self, db_session: AsyncSession, owner_user: User, agent_user: User):
        """Update escalation status"""
        escalation = Escalation(
            client_phone="+19998887777",
            user_id=owner_user.id,
            agent_id=agent_user.id,
            reason="Test escalation",
            status="pending",
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(escalation)
        await db_session.commit()
        
        # Update status
        escalation.status = "resolved"
        escalation.resolved_at = datetime.now(timezone.utc)
        await db_session.commit()
        
        # Verify
        result = await db_session.execute(
            select(Escalation).where(Escalation.id == escalation.id)
        )
        updated = result.scalar_one()
        assert updated.status == "resolved"
        assert updated.resolved_at is not None
        print(f"\n✓ Updated escalation status to: {updated.status}")


class TestDocumentOperations:
    """Test Document operations"""
    
    @pytest.mark.asyncio
    async def test_create_client_document(self, db_session: AsyncSession, owner_user: User):
        """Create a client document"""
        # First create a client
        client = Client(
            phone="+14443332222",
            name="Document Client",
            user_id=owner_user.id
        )
        db_session.add(client)
        await db_session.commit()
        await db_session.refresh(client)
        
        # Create document
        document = ClientDocument(
            client_id=client.id,
            user_id=owner_user.id,
            filename="contract.pdf",
            document_type="contract",
            file_path="/uploads/contracts/contract.pdf",
            uploaded_at=datetime.now(timezone.utc)
        )
        db_session.add(document)
        await db_session.commit()
        await db_session.refresh(document)
        
        assert document.id is not None
        assert document.document_type == "contract"
        print(f"\n✓ Created client document: {document.filename}")


class TestDatabaseTransactions:
    """Test transaction behavior"""
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, db_session: AsyncSession):
        """Test that failed transactions roll back"""
        user = User(
            name="Rollback Test",
            email="rollback@example.com",
            password_hash=generate_hash_password("password"),
            role=UserRole.OWNER,
            firstname="Rollback",
            lastname="Test"
        )
        db_session.add(user)
        await db_session.flush()
        
        user_id = user.id
        
        # Rollback manually
        await db_session.rollback()
        
        # Verify user was not committed
        result = await db_session.execute(
            select(User).where(User.id == user_id)
        )
        assert result.scalar_one_or_none() is None
        print(f"\n✓ Transaction rollback successful")
    
    @pytest.mark.asyncio
    async def test_bulk_insert(self, db_session: AsyncSession):
        """Test bulk insert of multiple records"""
        users = [
            User(
                name=f"Bulk User {i}",
                email=f"bulk{i}@example.com",
                password_hash=generate_hash_password("password"),
                role=UserRole.OWNER,
                firstname="Bulk",
                lastname=f"User{i}"
            )
            for i in range(10)
        ]
        
        db_session.add_all(users)
        await db_session.commit()
        
        # Verify all inserted
        result = await db_session.execute(
            select(User).where(User.email.like("bulk%@example.com"))
        )
        inserted = result.scalars().all()
        assert len(inserted) == 10
        print(f"\n✓ Bulk inserted {len(inserted)} users")
