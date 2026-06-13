from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("listings", "0008_listing_listings_li_owner_i_efae9b_idx_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS pg_trgm;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql=(
                "CREATE INDEX IF NOT EXISTS listings_listing_title_trgm_idx "
                "ON listings_listing USING GIN (title gin_trgm_ops);"
            ),
            reverse_sql="DROP INDEX IF EXISTS listings_listing_title_trgm_idx;",
        ),
        migrations.RunSQL(
            sql=(
                "CREATE INDEX IF NOT EXISTS listings_listing_description_trgm_idx "
                "ON listings_listing USING GIN (description gin_trgm_ops);"
            ),
            reverse_sql="DROP INDEX IF EXISTS listings_listing_description_trgm_idx;",
        ),
        migrations.RunSQL(
            sql=(
                "CREATE INDEX IF NOT EXISTS listings_listing_city_trgm_idx "
                "ON listings_listing USING GIN (city gin_trgm_ops);"
            ),
            reverse_sql="DROP INDEX IF EXISTS listings_listing_city_trgm_idx;",
        ),
        migrations.RunSQL(
            sql=(
                "CREATE INDEX IF NOT EXISTS listings_listing_search_vector_idx "
                "ON listings_listing USING GIN ("
                "to_tsvector('simple', "
                "coalesce(title, '') || ' ' || "
                "coalesce(description, '') || ' ' || "
                "coalesce(city, '') || ' ' || "
                "coalesce(county, '')"
                ")"
                ");"
            ),
            reverse_sql="DROP INDEX IF EXISTS listings_listing_search_vector_idx;",
        ),
    ]
