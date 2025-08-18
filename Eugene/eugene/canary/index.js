/* This might be irrelevant
const synthetics = require('Synthetics');
const log = require('SyntheticsLogger');

const simpleCanary = async function () {
    log.info("Starting the canary...");
    await synthetics.executeHttpStep('Verify Homepage', 'https://example.com');
    log.info("Finished the canary!");
};

exports.handler = simpleCanary;
*/

