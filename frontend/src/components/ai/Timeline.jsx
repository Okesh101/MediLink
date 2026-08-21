import { useEffect, useState } from "react";
import { Calendar, Clock, Activity, Hospital, UserCheck } from "lucide-react";
import { Spinner, Alert } from "../ui/Badge";
import { aiApi } from "../../services/ai";
import { getErrorMessage } from "../../services/api";

const eventIcons = {
  AI_CHAT: Activity,
  DISCHARGE: Hospital,
  FOLLOW_UP: Calendar,
  RECORD_ADDED: UserCheck,
  DEFAULT: Clock
};

const eventColors = {
  AI_CHAT: "bg-purple-100 text-purple-700 border-purple-200",
  DISCHARGE: "bg-green-100 text-green-700 border-green-200",
  FOLLOW_UP: "bg-blue-100 text-blue-700 border-blue-200",
  RECORD_ADDED: "bg-teal-100 text-teal-700 border-teal-200",
  DEFAULT: "bg-gray-100 text-gray-700 border-gray-200"
};

export default function Timeline() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const response = await aiApi.getTimeline();
        if (!cancelled) {
          setEvents(response.data.data || []);
        }
      } catch (err) {
        if (!cancelled) setError(getErrorMessage(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center py-10">
        <Spinner className="h-6 w-6" />
      </div>
    );
  }

  if (error) {
    return <Alert>{error}</Alert>;
  }

  if (events.length === 0) {
    return (
      <div className="text-center py-10 text-muted">
        <Calendar className="h-12 w-12 mx-auto mb-3 opacity-50" />
        <p>No timeline events yet</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {events.map((event, index) => {
        const Icon = eventIcons[event.event_type] || eventIcons.DEFAULT;
        const colorClass = eventColors[event.event_type] || eventColors.DEFAULT;
        
        return (
          <div key={event.id} className="flex gap-4">
            <div className="flex flex-col items-center">
              <div className={`p-2 rounded-full border ${colorClass}`}>
                <Icon className="h-4 w-4" />
              </div>
              {index < events.length - 1 && (
                <div className="w-0.5 h-full bg-gray-200 mt-2" />
              )}
            </div>
            <div className="flex-1 pb-6">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="font-medium text-gray-900">{event.title}</h4>
                  <p className="text-sm text-muted mt-1">{event.description}</p>
                </div>
                <div className="text-right text-xs text-muted">
                  <div className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {new Date(event.created_at).toLocaleDateString()}
                  </div>
                  <div className="mt-1">
                    {new Date(event.created_at).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
