import re

FILTERABLE_COLUMNS = [
    'ID',
    'Number',
    'Members_Name',
    'Member_Type',
    'Paid_Up_2026',
    'Paused',
    'E_Mail',
    'Mobile',
    'Car_Reg',
    'EA_Licence',
    'Licence_Exp',
    'Resigned',
]

LEGACY_TO_POSTGRES_MEMBER_COLUMNS = {
    'ID': 'legacy_id',
    'Number': 'number',
    'Members_Name': 'members_name',
    'Title': 'title',
    'First_Name': 'first_name',
    'Last_Name': 'last_name',
    'Photo_Path': 'photo_path',
    'Preferred_Name': 'preferred_name',
    'First_Names': 'first_names',
    'Paused': 'paused',
    'Resigned': 'resigned',
    'Member_Type': 'member_type',
    'Subs_Expected': 'subs_expected',
    'Subs_paid': 'subs_paid',
    'Join_Fee': 'join_fee',
    'Paid_Up_2026': 'paid_up_2026',
    'Photo_Received': 'photo_received',
    'In_WhatsApp': 'in_whatsapp',
    'In_FB': 'in_fb',
    'Date_of_Birth': 'date_of_birth',
    'Age': 'age',
    'New_Member_2026': 'new_member_2026',
    'Paid_up_Card_Sent': 'paid_up_card_sent',
    'CR2023': 'cr2023',
    'CR2024': 'cr2024',
    'CR2025': 'cr2025',
    'Details_Confirmed_2026': 'details_confirmed_2026',
    'Full_Address': 'full_address',
    'Address___Street_Address': 'address_street',
    'Address___Address_Line_2': 'address_line_2',
    'Address___City': 'address_city',
    'County': 'county',
    'Address___State/Prov/Region': 'address_state_region',
    'Address___ZIP/Postal': 'address_zip_postal',
    'Address___Country': 'address_country',
    'Phone': 'phone',
    'Mobile': 'mobile',
    'E_Mail': 'email',
    'EA_Licence': 'ea_licence',
    'Licence_Exp': 'licence_exp',
    'Car_Reg': 'car_reg',
    'username': 'username',
    'password': 'password',
}

NEWSLETTER_TEMPLATES = {
    'club-update': {
        'id': 'club-update',
        'name': 'Club Update',
        'subject': '<Club> Newsletter Update',
        'body': (
            'Dear <Title> <Last_Name>,\n\n'
            'This is your latest newsletter update from <Club>.\n\n'
            'Your membership number is <Number>.\n\n'
            'Kind regards,\n'
            '<Club> Committee'
        ),
    },
    'membership-reminder': {
        'id': 'membership-reminder',
        'name': 'Membership Reminder',
        'subject': '<Club> Membership Reminder',
        'body': (
            'Hello <Preferred_Name>,\n\n'
            'This is a friendly reminder from <Club> regarding your membership renewal.\n\n'
            'Name:   <Members_Name>\n'
            'Number: <Number>\n\n'
            'Please ensure your subscription is up to date.\n\n'
            'Kind regards,\n'
            '<Club> Committee'
        ),
    },
}

NEWSLETTER_TEMPLATE_TAGS = [
    {'tag': 'Club', 'description': 'Club name', 'source': 'special'},
    {'tag': 'Title', 'description': "Member's title (Mr/Mrs/etc)", 'source': 'column'},
    {'tag': 'First_Name', 'description': "Member's first name", 'source': 'column'},
    {'tag': 'Last_Name', 'description': "Member's last name", 'source': 'column'},
    {'tag': 'Preferred_Name', 'description': "Member's preferred name", 'source': 'column'},
    {'tag': 'Members_Name', 'description': 'Full name (as stored)', 'source': 'column'},
    {'tag': 'Number', 'description': 'Membership number', 'source': 'column'},
    {'tag': 'Member_Type', 'description': 'Membership type', 'source': 'column'},
    {'tag': 'E_Mail', 'description': "Member's email address", 'source': 'column'},
]

_TEMPLATE_TAG_RE = re.compile(r'<([A-Za-z_][A-Za-z0-9_]*)>')


def render_newsletter_template(template_str: str, context: dict) -> str:
    return _TEMPLATE_TAG_RE.sub(
        lambda m: str(context.get(m.group(1), m.group(0))),
        template_str,
    )


def normalize_what3words_value(raw_value):
    value = str(raw_value or '').strip()
    if not value:
        return ''

    without_slashes = re.sub(r'^/+', '', value).strip()
    words = [word.strip() for word in without_slashes.split('.')]

    if len(words) != 3 or any(not word for word in words):
        return value

    if not all(re.fullmatch(r'[A-Za-z]+', word) for word in words):
        return value

    return f"///{'.'.join(word.lower() for word in words)}"


def normalize_parking_locations(parking_source):
    if not isinstance(parking_source, list):
        return []

    normalized = []
    for location in parking_source:
        if not isinstance(location, dict):
            continue
        normalized.append({
            'Name': str(location.get('Name', '')).strip(),
            'Location': normalize_what3words_words(location.get('Location', '')),
            'Description': str(location.get('Description', '')).strip(),
            'Latitude': str(location.get('Latitude', '')).strip(),
            'Longitude': str(location.get('Longitude', '')).strip(),
        })

    return normalized


def normalize_what3words_words(raw_value):
    value = str(raw_value or '').strip()
    if not value:
        return ''

    without_slashes = re.sub(r'^/+', '', value).strip().lower()
    words = [word.strip() for word in without_slashes.split('.')]

    if len(words) != 3 or any(not word for word in words):
        return ''

    if not all(re.fullmatch(r'[a-z]+', word) for word in words):
        return ''

    return '.'.join(words)


def normalize_beats(beats_source):
    if not isinstance(beats_source, list):
        return []

    normalized = []
    for beat in beats_source:
        if not isinstance(beat, dict):
            continue

        beat_upstream = str(beat.get('Beat_Upstream', '')).strip()
        beat_downstream = str(beat.get('Beat_Downstream', '')).strip()

        normalized.append({
            'Beat_Name': str(beat.get('Beat_Name', '')).strip(),
            'Beat_ID': str(beat.get('Beat_ID', '')).strip(),
            'River': str(beat.get('River', '')).strip(),
            'Position': str(beat.get('Position', '')).strip(),
            'Beat_Upstream': normalize_what3words_value(beat_upstream),
            'Beat_Downstream': normalize_what3words_value(beat_downstream),
            'Beat_Description': str(beat.get('Beat_Description', '')).strip(),
            'Detailed_Description': str(beat.get('Detailed_Description', '')).strip(),
            'Beat_Upstream_Latitude': str(beat.get('Beat_Upstream_Latitude', '')).strip(),
            'Beat_Upstream_Longitude': str(beat.get('Beat_Upstream_Longitude', '')).strip(),
            'Beat_Downstream_Latitude': str(beat.get('Beat_Downstream_Latitude', '')).strip(),
            'Beat_Downstream_Longitude': str(beat.get('Beat_Downstream_Longitude', '')).strip(),
            'Parking_Locations': normalize_parking_locations(beat.get('Parking_Locations', [])),
        })

    return normalized


def wildcard_to_sql_like(value):
    escaped = value.replace('\\', '\\\\')
    escaped = escaped.replace('%', '\\%').replace('_', '\\_')
    escaped = escaped.replace('*', '%').replace('?', '_')
    return escaped


def normalize_newsletter_filters(filters_source):
    if not isinstance(filters_source, dict):
        return {}

    normalized = {}
    for column_name in FILTERABLE_COLUMNS:
        raw_filter = filters_source.get(column_name)
        if raw_filter is None:
            continue

        filter_value = str(raw_filter).strip()
        if not filter_value:
            continue

        if filter_value == '[BLANK]':
            normalized[column_name] = '[BLANK]'
            continue

        has_wildcard = ('*' in filter_value) or ('?' in filter_value)
        normalized[column_name] = filter_value if has_wildcard else f'*{filter_value}*'

    return normalized
