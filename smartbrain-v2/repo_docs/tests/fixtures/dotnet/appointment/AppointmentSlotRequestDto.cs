// Fixture: trimmed reproduction of appointment-booking-service
// src/Appointment.Application/Appointment/Dtos/AppointmentSlotRequestDto.cs (+ Output model).
using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;

namespace Appointment.Application.Appointment.Dtos
{
    public class AppointmentSlotRequestDto
    {
        [Required]
        public int dealerId { get; set; }
        public int branchId { get; set; }
        [JsonPropertyName("from_date")]
        public DateTime? fromDate { get; set; }
        [StringLength(20, MinimumLength = 2)]
        public string? channel { get; set; }
        [JsonIgnore]
        public string Internal { get; set; } = "";
        public SlotKind Kind { get; set; }
    }

    public enum SlotKind { Morning = 1, Evening = 2 }

    public class Output
    {
        public int statusCode { get; set; }
        public string message { get; set; } = "";
    }

    public record Success(long appointmentId, DateTime? appointmentDateTime);
}
