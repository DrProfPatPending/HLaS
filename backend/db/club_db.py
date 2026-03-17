import os

from sqlalchemy import Column, Date, Integer, MetaData, PrimaryKeyConstraint, String, Table, and_, cast, create_engine, select
from sqlalchemy.orm import registry, sessionmaker

from core.common import NEWSLETTER_TEMPLATES
from db.postgres_backend import get_postgres_backend, is_postgres_reads_enabled

DB_DIR = os.path.dirname(os.path.dirname(__file__))
APP_DATA_DIR = os.getenv('HLAS_DATA_DIR', DB_DIR)

_club_db_cache = {}


def ensure_newsletter_templates_table(engine):
    inspector_metadata = MetaData()
    inspector_metadata.reflect(bind=engine)

    if 'newsletter_templates' not in inspector_metadata.tables:
        template_metadata = MetaData()
        Table(
            'newsletter_templates',
            template_metadata,
            Column('id', String, primary_key=True),
            Column('name', String, nullable=False),
            Column('subject', String, nullable=False),
            Column('body', String, nullable=False),
        )
        template_metadata.create_all(bind=engine)

        with engine.connect() as conn:
            conn.execute(
                '''INSERT INTO newsletter_templates (id, name, subject, body) VALUES (?, ?, ?, ?)''',
                [
                    (
                        NEWSLETTER_TEMPLATES['club-update']['id'],
                        NEWSLETTER_TEMPLATES['club-update']['name'],
                        NEWSLETTER_TEMPLATES['club-update']['subject'],
                        NEWSLETTER_TEMPLATES['club-update']['body'],
                    ),
                    (
                        NEWSLETTER_TEMPLATES['membership-reminder']['id'],
                        NEWSLETTER_TEMPLATES['membership-reminder']['name'],
                        NEWSLETTER_TEMPLATES['membership-reminder']['subject'],
                        NEWSLETTER_TEMPLATES['membership-reminder']['body'],
                    ),
                ],
            )
            conn.commit()


def get_db_for_club(club):
    if club not in _club_db_cache:
        db_path = os.path.join(APP_DATA_DIR, f'{club}.db')
        database_url = f"sqlite:///{db_path.replace(os.sep, '/')}"
        engine = create_engine(database_url, future=True)
        session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

        ensure_newsletter_templates_table(engine)

        mapper_registry = registry()
        metadata = mapper_registry.metadata
        members_table = Table('members', metadata, autoload_with=engine)
        newsletter_templates_table = Table('newsletter_templates', metadata, autoload_with=engine)

        if len(members_table.primary_key.columns) == 0:
            fallback_primary_key = None
            for candidate_key in ('ID', 'id', 'Number', 'username'):
                if candidate_key in members_table.c:
                    fallback_primary_key = candidate_key
                    break
            if fallback_primary_key is None:
                raise RuntimeError(f'Could not determine a primary key for members table in {club}.db')
            members_table.append_constraint(PrimaryKeyConstraint(members_table.c[fallback_primary_key]))

        class Member:
            pass

        mapper_registry.map_imperatively(Member, members_table)

        _club_db_cache[club] = {
            'engine': engine,
            'session_factory': session_factory,
            'mapper_registry': mapper_registry,
            'metadata': metadata,
            'members_table': members_table,
            'newsletter_templates_table': newsletter_templates_table,
            'Member': Member,
        }

    cache = _club_db_cache[club]
    session = cache['session_factory']()
    return {
        'session': session,
        'engine': cache['engine'],
        'members_table': cache['members_table'],
        'newsletter_templates_table': cache['newsletter_templates_table'],
        'Member': cache['Member'],
        'mapper_registry': cache['mapper_registry'],
    }


def get_read_db_for_club(club):
    if not is_postgres_reads_enabled():
        return get_db_for_club(club)

    backend = get_postgres_backend()
    if club not in backend['read_club_cache']:
        session = backend['session_factory']()
        clubs_table = backend['clubs_table']
        members_base_table = backend['members_table']
        newsletter_base_table = backend['newsletter_templates_table']

        try:
            club_id = session.execute(
                select(clubs_table.c.id).where(
                    and_(clubs_table.c.short_name == club, clubs_table.c.is_active.is_(True))
                )
            ).scalar_one_or_none()
        finally:
            session.close()

        if club_id is None:
            raise RuntimeError(f'Club {club} not found in PostgreSQL')

        mapper_registry = registry()
        members_query = select(
            members_base_table.c.id.label('ID'),
            members_base_table.c.number.label('Number'),
            members_base_table.c.members_name.label('Members_Name'),
            members_base_table.c.title.label('Title'),
            members_base_table.c.first_name.label('First_Name'),
            members_base_table.c.last_name.label('Last_Name'),
            members_base_table.c.photo_path.label('Photo_Path'),
            members_base_table.c.preferred_name.label('Preferred_Name'),
            members_base_table.c.first_names.label('First_Names'),
            members_base_table.c.paused.label('Paused'),
            members_base_table.c.resigned.label('Resigned'),
            members_base_table.c.member_type.label('Member_Type'),
            members_base_table.c.subs_expected.label('Subs_Expected'),
            members_base_table.c.subs_paid.label('Subs_paid'),
            members_base_table.c.join_fee.label('Join_Fee'),
            members_base_table.c.paid_up_2026.label('Paid_Up_2026'),
            members_base_table.c.photo_received.label('Photo_Received'),
            members_base_table.c.in_whatsapp.label('In_WhatsApp'),
            members_base_table.c.in_fb.label('In_FB'),
            cast(members_base_table.c.date_of_birth, String).label('Date_of_Birth'),
            members_base_table.c.age.label('Age'),
            members_base_table.c.new_member_2026.label('New_Member_2026'),
            members_base_table.c.paid_up_card_sent.label('Paid_up_Card_Sent'),
            members_base_table.c.cr2023.label('CR2023'),
            members_base_table.c.cr2024.label('CR2024'),
            members_base_table.c.cr2025.label('CR2025'),
            members_base_table.c.details_confirmed_2026.label('Details_Confirmed_2026'),
            members_base_table.c.full_address.label('Full_Address'),
            members_base_table.c.address_street.label('Address___Street_Address'),
            members_base_table.c.address_line_2.label('Address___Address_Line_2'),
            members_base_table.c.address_city.label('Address___City'),
            members_base_table.c.county.label('County'),
            members_base_table.c.address_state_region.label('Address___State/Prov/Region'),
            members_base_table.c.address_zip_postal.label('Address___ZIP/Postal'),
            members_base_table.c.address_country.label('Address___Country'),
            members_base_table.c.phone.label('Phone'),
            members_base_table.c.mobile.label('Mobile'),
            members_base_table.c.email.label('E_Mail'),
            members_base_table.c.ea_licence.label('EA_Licence'),
            members_base_table.c.licence_exp.label('Licence_Exp'),
            members_base_table.c.car_reg.label('Car_Reg'),
            members_base_table.c.username.label('username'),
            members_base_table.c.password.label('password'),
        ).where(members_base_table.c.club_id == club_id).subquery(f'{club.lower()}_members_read')

        newsletter_query = select(
            newsletter_base_table.c.template_key.label('id'),
            newsletter_base_table.c.name.label('name'),
            newsletter_base_table.c.subject.label('subject'),
            newsletter_base_table.c.body.label('body'),
        ).where(newsletter_base_table.c.club_id == club_id).subquery(f'{club.lower()}_newsletter_templates_read')

        class Member:
            pass

        mapper_registry.map_imperatively(Member, members_query, primary_key=[members_query.c.ID])
        backend['read_club_cache'][club] = {
            'club_id': club_id,
            'mapper_registry': mapper_registry,
            'members_table': members_query,
            'newsletter_templates_table': newsletter_query,
            'Member': Member,
        }

    cache = backend['read_club_cache'][club]
    session = backend['session_factory']()
    return {
        'session': session,
        'engine': backend['engine'],
        'members_table': cache['members_table'],
        'newsletter_templates_table': cache['newsletter_templates_table'],
        'Member': cache['Member'],
        'mapper_registry': cache['mapper_registry'],
        'club_id': cache['club_id'],
    }


def initialize_database(club):
    db_path = os.path.join(APP_DATA_DIR, f'{club}.db')
    database_url = f"sqlite:///{db_path.replace(os.sep, '/')}"
    engine = create_engine(database_url, future=True)
    bootstrap_metadata = MetaData()
    Table(
        'members',
        bootstrap_metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('name', String, nullable=False),
        Column('email', String),
        Column('phone', String),
        Column('membership_type', String),
        Column('password', String),
    )
    bootstrap_metadata.create_all(bind=engine)
