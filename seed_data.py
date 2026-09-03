"""
Seed data script for WhatsApp Conveyancing Bot
Populates MongoDB with 20 conveyancers for paginated display
"""
import asyncio
import sys
from app.database import connect_to_mongodb, close_mongodb_connection, get_database


# 20 conveyancers sorted alphabetically for consistent pagination
CONVEYANCERS = [
    {
        "company_name": "African Legal Consultants",
        "contact_person": "Sarah Moyo",
        "email": "sarah.moyo@africanlegal.co.zw",
        "phone_number": "+263712345678",
        "tin_number": "1001234567",
        "province": "Harare"
    },
    {
        "company_name": "Beitbridge Law Firm",
        "contact_person": "John Nkomo",
        "email": "john.nkomo@beitbridgelaw.co.zw",
        "phone_number": "+263712345679",
        "tin_number": "1001234568",
        "province": "Masvingo"
    },
    {
        "company_name": "Chinhoyi Legal Associates",
        "contact_person": "Grace Chivasa",
        "email": "grace.chivasa@chinhoyilegal.co.zw",
        "phone_number": "+263712345680",
        "tin_number": "1001234569",
        "province": "Mashonaland West"
    },
    {
        "company_name": "Delta Law Chambers",
        "contact_person": "Peter Dube",
        "email": "peter.dube@delta-law.co.zw",
        "phone_number": "+263712345681",
        "tin_number": "1001234570",
        "province": "Bulawayo"
    },
    {
        "company_name": "Equity Legal Practitioners",
        "contact_person": "Martha Kademaunga",
        "email": "martha.kademaunga@equitylegal.co.zw",
        "phone_number": "+263712345682",
        "tin_number": "1001234571",
        "province": "Harare"
    },
    {
        "company_name": "Fortress Attorneys",
        "contact_person": "Brian Mutasa",
        "email": "brian.mutasa@fortressattorneys.co.zw",
        "phone_number": "+263712345683",
        "tin_number": "1001234572",
        "province": "Manicaland"
    },
    {
        "company_name": "Gweru Law Partners",
        "contact_person": "Chengeto Mhlanga",
        "email": "chengeto.mhlanga@gwerulaw.co.zw",
        "phone_number": "+263712345684",
        "tin_number": "1001234573",
        "province": "Midlands"
    },
    {
        "company_name": "Harare Conveyancing Specialists",
        "contact_person": "Lloyd Shingai Toendepi",
        "email": "ltoendepi@gmail.com",
        "phone_number": "+263773365742",
        "tin_number": "2001512841",
        "province": "Harare"
    },
    {
        "company_name": "Inkomo Legal Services",
        "contact_person": "Nkosana Mpofu",
        "email": "nkosana.mpofu@inkomolegal.co.zw",
        "phone_number": "+263712345685",
        "tin_number": "1001234574",
        "province": "Matabeleland North"
    },
    {
        "company_name": "Justice Chambers",
        "contact_person": "Rumbidzai Moyo",
        "email": "rumbidzai.moyo@justicechambers.co.zw",
        "phone_number": "+263712345686",
        "tin_number": "1001234575",
        "province": "Harare"
    },
    {
        "company_name": "Kwekwe Legal Consultants",
        "contact_person": "Tawanda Chikwinya",
        "email": "tawanda.chikwinya@kwekwelegal.co.zw",
        "phone_number": "+263712345687",
        "tin_number": "1001234576",
        "province": "Midlands"
    },
    {
        "company_name": "Marondera Law Firm",
        "contact_person": "Precious Mashiri",
        "email": "precious.mashiri@maronderalaw.co.zw",
        "phone_number": "+263712345688",
        "tin_number": "1001234577",
        "province": "Mashonaland East"
    },
    {
        "company_name": "Mutare Legal Associates",
        "contact_person": "Simbarashe Nyamukondiwa",
        "email": "simbarashe.nyamukondiwa@mutarelegal.co.zw",
        "phone_number": "+263712345689",
        "tin_number": "1001234578",
        "province": "Manicaland"
    },
    {
        "company_name": "Ndola Conveyancing Services",
        "contact_person": "Patience Zinyemba",
        "email": "patience.zinyemba@ndolalaw.co.zw",
        "phone_number": "+263712345690",
        "tin_number": "1001234579",
        "province": "Mashonaland Central"
    },
    {
        "company_name": "Omega Legal Practitioners",
        "contact_person": "Gerald Muzenda",
        "email": "gerald.muzenda@omegalegal.co.zw",
        "phone_number": "+263712345691",
        "tin_number": "1001234580",
        "province": "Bulawayo"
    },
    {
        "company_name": "Platinum Law Chambers",
        "contact_person": "Violet Hlatshwayo",
        "email": "violet.hlatshwayo@platinumlaw.co.zw",
        "phone_number": "+263712345692",
        "tin_number": "1001234581",
        "province": "Matabeleland South"
    },
    {
        "company_name": "Queensbury Attorneys",
        "contact_person": "Charles Manyika",
        "email": "charles.manyika@queensbury.co.zw",
        "phone_number": "+263712345693",
        "tin_number": "1001234582",
        "province": "Harare"
    },
    {
        "company_name": "Rusape Legal Services",
        "contact_person": "Lydia Machona",
        "email": "lydia.machona@rusapelegal.co.zw",
        "phone_number": "+263712345694",
        "tin_number": "1001234583",
        "province": "Manicaland"
    },
    {
        "company_name": "Shamva Law Partners",
        "contact_person": "Moses Mlambo",
        "email": "moses.mlambo@shamvalaw.co.zw",
        "phone_number": "+263712345695",
        "tin_number": "1001234584",
        "province": "Mashonaland Central"
    },
    {
        "company_name": "Zimbabwe Conveyancing Bureau",
        "contact_person": "Tendai Chirimukutu",
        "email": "tendai.chirimukutu@zimbabweconveyancing.co.zw",
        "phone_number": "+263712345696",
        "tin_number": "1001234585",
        "province": "Harare"
    }
]


async def seed_conveyancers():
    """
    Seed the conveyancers collection with 20 law firms
    """
    try:
        # Connect to MongoDB
        await connect_to_mongodb()
        database = get_database()
        
        # Clear existing conveyancers (optional - comment out if you want to keep existing data)
        await database.conveyancers.delete_many({})
        print("Cleared existing conveyancers collection")
        
        # Insert conveyancers
        result = await database.conveyancers.insert_many(CONVEYANCERS)
        print(f"Successfully inserted {len(result.inserted_ids)} conveyancers")
        
        # Verify insertion
        count = await database.conveyancers.count_documents({})
        print(f"Total conveyancers in database: {count}")
        
        # Display first few conveyancers
        print("\nFirst 5 conveyancers (alphabetical order):")
        cursor = database.conveyancers.find().sort("company_name", 1).limit(5)
        async for conveyancer in cursor:
            print(f"  - {conveyancer['company_name']} ({conveyancer['province']})")
        
    except Exception as e:
        print(f"Error seeding conveyancers: {e}")
        raise
    finally:
        await close_mongodb_connection()


if __name__ == "__main__":
    print("Starting conveyancers seed data script...")
    asyncio.run(seed_conveyancers())
    print("Seed data script completed successfully!")