const { app } = require('@azure/functions');
const productPriceIngestionJob = require('../product-price-ingestion-job');

app.timer('product-price-ingestion-job', {
    runOnStartup: false,
    schedule: process.env.CRON_EXPRESSION_FOR_PRODUCT_PRICE_INGESTION_JOB,
    handler: async (myTimer, context) => {
        await productPriceIngestionJob.run(context);
    }
});
