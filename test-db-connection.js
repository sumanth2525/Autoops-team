// Test SQL Server Connection
const sql = require('mssql');
require('dotenv').config();

const dbConfig = {
    server: process.env.DB_SERVER || 'SUMANTH\\SQLEXPRESS',
    database: process.env.DB_NAME || 'AutoOpsDB',
    user: process.env.DB_USER || '',
    password: process.env.DB_PASSWORD || '',
    options: {
        encrypt: process.env.DB_ENCRYPT === 'true',
        trustServerCertificate: true,
        enableArithAbort: true,
        connectionTimeout: 10000
    }
};

// Use Windows Authentication if no user/password provided
if (!dbConfig.user && !dbConfig.password) {
    dbConfig.options.trustedConnection = true;
}

async function testConnection() {
    console.log('🔍 Testing SQL Server connection...');
    console.log(`   Server: ${dbConfig.server}`);
    console.log(`   Database: ${dbConfig.database}`);
    console.log(`   Authentication: ${dbConfig.options.trustedConnection ? 'Windows' : 'SQL Server'}`);
    console.log('');

    // Try different server name formats
    const serverVariations = [
        dbConfig.server,  // Original
        'localhost\\SQLEXPRESS',
        '.\\SQLEXPRESS',
        '(local)\\SQLEXPRESS',
        'SUMANTH\\SQLEXPRESS',
        '127.0.0.1\\SQLEXPRESS'
    ];

    for (const serverName of serverVariations) {
        try {
            console.log(`   Trying: ${serverName}...`);
            const testConfig = { ...dbConfig, server: serverName };
            const masterConfig = { ...testConfig, database: 'master' };
            const pool = await sql.connect(masterConfig);
        console.log('✅ Successfully connected to SQL Server!');
        
        // Check if database exists
        const request = pool.request();
        const result = await request.query(`
            SELECT name FROM sys.databases WHERE name = '${dbConfig.database}'
        `);
        
        if (result.recordset.length > 0) {
            console.log(`✅ Database "${dbConfig.database}" exists`);
            
            // Try to connect to the actual database
            await pool.close();
            const dbPool = await sql.connect(dbConfig);
            console.log(`✅ Successfully connected to database "${dbConfig.database}"`);
            await dbPool.close();
            console.log('\n🎉 All checks passed! Database is ready.');
        } else {
            console.log(`⚠️  Database "${dbConfig.database}" does NOT exist`);
            console.log('\n📝 To create the database, run this in SSMS:');
            console.log(`   CREATE DATABASE ${dbConfig.database};`);
            console.log('\n   Or run the database-schema.sql script.');
        }
        
            await pool.close();
            console.log(`\n✅ SUCCESS! Working server name: ${serverName}`);
            console.log(`\n📝 Update your .env file with:`);
            console.log(`   DB_SERVER=${serverName}`);
            process.exit(0);
        } catch (err) {
            // Try next variation
            continue;
        }
    }
    
    // If we get here, all variations failed
    console.error('\n❌ All connection attempts failed!');
    console.error('\n🔧 Troubleshooting steps:');
    console.error('   1. Open SQL Server Management Studio (SSMS)');
    console.error('   2. Try to connect and note the exact server name that works');
    console.error('   3. Update DB_SERVER in .env file with that exact name');
    console.error('   4. Make sure SQL Server (SQLEXPRESS) service is running');
    console.error('   5. Check Windows Firewall settings');
    process.exit(1);
}

testConnection();

