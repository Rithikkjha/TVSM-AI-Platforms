// Fixture: trimmed reproduction of PaymentService Functions/JusPayWebhooks.cs (isolated worker,
// [ServiceBusTrigger("cpg-juspay")] at the same relative position) plus an HTTP + timer function.
using Azure.Messaging.ServiceBus;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using PaymentService.Constants;
namespace PaymentService.Functions
{
    public class JusPayWebhooks
    {
        [Function(nameof(JusPayWebhooks))]
        public async Task Run(
            [ServiceBusTrigger("cpg-juspay")]
            ServiceBusReceivedMessage message,
            ServiceBusMessageActions messageActions)
        {
            var token = await GenerateToken(null);
            await messageActions.DeadLetterMessageAsync(message);
        }

        public async Task<string> GenerateToken(object data)
        {
            HttpClient client = new HttpClient();
            HttpRequestMessage request = new HttpRequestMessage(HttpMethod.Post, Environment.GetEnvironmentVariable(General.TokenUrl));
            HttpResponseMessage response = await client.SendAsync(request);
            return await response.Content.ReadAsStringAsync();
        }

        [Function("PaymentStatus")]
        public HttpResponseData Status(
            [HttpTrigger(AuthorizationLevel.Function, "get", Route = "payments/{orderId:int}/status")] HttpRequestData req,
            int orderId)
        {
            return req.CreateResponse();
        }

        [Function("Reconcile")]
        public void Reconcile([TimerTrigger("%ReconcileSchedule%")] TimerInfo timer)
        {
        }

        [Function("Refunds")]
        public void Refunds([ServiceBusTrigger("%RefundTopic%", "%RefundSubscription%", Connection = "ServiceBusConnection")] string body)
        {
        }
    }
}
