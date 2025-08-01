module.exports = async function (context, req) {
    const subscriptionKey = process.env.AZURE_SPEECH_KEY;
    const region = process.env.AZURE_SPEECH_REGION;
    
    if (!subscriptionKey) {
        context.res = {
            status: 500,
            body: { error: 'Speech service key not configured' }
        };
        return;
    }

    const tokenUrl = `https://${region}.api.cognitive.microsoft.com/sts/v1.0/issueToken`;
    
    try {
        const response = await fetch(tokenUrl, {
            method: 'POST',
            headers: {
                'Ocp-Apim-Subscription-Key': subscriptionKey,
                'Content-Length': '0'
            }
        });

        if (response.ok) {
            const token = await response.text();
            context.res = {
                status: 200,
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                body: { token, region }
            };
        } else {
            throw new Error(`HTTP ${response.status}`);
        }

    } catch (error) {
        context.log.error('Token generation failed:', error);
        context.res = {
            status: 500,
            body: { error: 'Failed to generate token' }
        };
    }
};