// Fixture: trimmed reproduction of BS2.0Backend_Integration QueueDispatcher/Dispatcher.cs
// (dynamic queue name passed in by the caller; the endpoint constant value is FAKE).
using Azure.Messaging.ServiceBus;

namespace CustomerBay.QueueDispatcher
{
    public static class Constants
    {
        public const string SERVICE_BUS_ENDPOINT = "Endpoint=sb://fake-bs2-ns.servicebus.windows.net/;SharedAccessKeyName=send;SharedAccessKey=fakeBs2SbKey0123456789abcdef=";
    }

    public class Dispatcher
    {
        private readonly ServiceBusClient client = new(Constants.SERVICE_BUS_ENDPOINT);
        public async Task Dispatch(string queueName, string message)
        {
            var sender = client.CreateSender(queueName);
            var busMessage = new ServiceBusMessage(message) { Subject = "booking-export", SessionId = message };
            await sender.SendMessageAsync(busMessage);
        }
    }
}
