"""
Conditional document logic for service-specific requirements
Handles dynamic document requirements based on user responses
"""
from typing import Dict, Any, List, Optional
from app.models import ServiceType


class ConditionalDocumentLogic:
    """Manages conditional document requirements based on user responses"""
    
    @staticmethod
    def get_property_type_questions(service_type: ServiceType) -> List[Dict[str, Any]]:
        """
        Get property type questions that determine conditional document requirements
        
        Args:
            service_type: The type of conveyancing service
            
        Returns:
            List of questions to ask the user
        """
        questions = {
            ServiceType.DEED_OF_TRANSFER: [
                {
                    "question": "What type of property is this?",
                    "options": [
                        {"id": "stand_alone_house", "text": "Standalone house/stand"},
                        {"id": "sectional_title", "text": "Sectional title/flat/cluster"},
                        {"id": "commercial", "text": "Commercial property"}
                    ],
                    "condition": "sectional_title",
                    "conditional_document": "levy_clearance"
                }
            ],
            ServiceType.DEED_OF_RECTIFICATION: [
                {
                    "question": "What type of rectification is needed?",
                    "options": [
                        {"id": "clerical_error", "text": "Clerical error (names, numbers, spelling)"},
                        {"id": "spatial_error", "text": "Spatial/boundary error"}
                    ],
                    "condition": "spatial_rectification",
                    "conditional_document": "corrected_sg_diagram"
                }
            ],
            ServiceType.DEED_OF_PARTITION: [
                {
                    "question": "How many joint owners are there?",
                    "options": [
                        {"id": "two_owners", "text": "2 owners"},
                        {"id": "three_owners", "text": "3 owners"},
                        {"id": "four_plus_owners", "text": "4 or more owners"}
                    ],
                    "condition": "multiple_owners",
                    "affects_document": "joint_owner_ids"
                }
            ]
        }
        
        return questions.get(service_type, [])
    
    @staticmethod
    def evaluate_conditional_documents(
        service_type: ServiceType,
        user_responses: Dict[str, str]
    ) -> Dict[str, bool]:
        """
        Evaluate which conditional documents are required based on user responses
        
        Args:
            service_type: The type of conveyancing service
            user_responses: Dictionary of user responses to property type questions
            
        Returns:
            Dictionary mapping condition names to boolean values
        """
        conditional_docs = {}
        
        # Evaluate based on service type and responses
        if service_type == ServiceType.DEED_OF_TRANSFER:
            # Levy clearance only for sectional title
            property_type = user_responses.get("property_type")
            conditional_docs["sectional_title"] = (property_type == "sectional_title")
        
        elif service_type == ServiceType.DEED_OF_RECTIFICATION:
            # Corrected SG diagram only for spatial rectification
            rectification_type = user_responses.get("rectification_type")
            conditional_docs["spatial_rectification"] = (rectification_type == "spatial_error")
        
        elif service_type == ServiceType.DEED_OF_PARTITION:
            # Multiple IDs based on number of owners
            owners_count = user_responses.get("owners_count")
            conditional_docs["multiple_owners"] = owners_count in ["three_owners", "four_plus_owners"]
        
        return conditional_docs
    
    @staticmethod
    def get_conditional_document_info(
        service_type: ServiceType,
        condition: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get information about a conditional document requirement
        
        Args:
            service_type: The type of conveyancing service
            condition: The condition name
            
        Returns:
            Dictionary with condition information or None
        """
        condition_info = {
            ServiceType.DEED_OF_TRANSFER: {
                "sectional_title": {
                    "document": "levy_clearance",
                    "question": "Is this a sectional title property (flat/cluster)?",
                    "required_if": "sectional_title",
                    "explanation": "Levy clearance certificate is only required for sectional title properties"
                }
            },
            ServiceType.DEED_OF_RECTIFICATION: {
                "spatial_rectification": {
                    "document": "corrected_sg_diagram",
                    "question": "Does this rectification involve spatial/boundary changes?",
                    "required_if": "spatial_error",
                    "explanation": "Corrected Surveyor General diagram is only required for spatial rectifications"
                }
            },
            ServiceType.DEED_OF_PARTITION: {
                "multiple_owners": {
                    "document": "joint_owner_ids",
                    "question": "Are there more than 2 joint owners?",
                    "required_if": "three_owners",
                    "explanation": "Additional ID documents are required for each joint owner"
                }
            }
        }
        
        return condition_info.get(service_type, {}).get(condition)
    
    @staticmethod
    def should_require_document(
        document_id: str,
        conditional_docs: Dict[str, bool]
    ) -> bool:
        """
        Determine if a conditional document should be required
        
        Args:
            document_id: The document identifier
            conditional_docs: Dictionary of conditional document decisions
            
        Returns:
            True if document should be required, False otherwise
        """
        from app.document_sequences import get_document_requirements
        
        doc_info = get_document_requirements(document_id)
        
        # If document is not conditional, it's always required
        if not doc_info.get("conditional"):
            return True
        
        # Check the condition
        condition = doc_info.get("condition")
        return conditional_docs.get(condition, False)
    
    @staticmethod
    def get_property_type_prompts(service_type: ServiceType) -> List[str]:
        """
        Get WhatsApp message prompts for property type questions
        
        Args:
            service_type: The type of conveyancing service
            
        Returns:
            List of message prompts to send to user
        """
        questions = ConditionalDocumentLogic.get_property_type_questions(service_type)
        prompts = []
        
        for i, question in enumerate(questions):
            prompt = f"Question {i + 1}: {question['question']}\n\n"
            
            for j, option in enumerate(question['options'], 1):
                prompt += f"{j}. {option['text']}\n"
            
            prompt += "\nPlease reply with the number of your choice."
            prompts.append(prompt)
        
        return prompts
    
    @staticmethod
    def parse_property_type_response(
        service_type: ServiceType,
        question_index: int,
        response: str
    ) -> Optional[str]:
        """
        Parse user response to property type question
        
        Args:
            service_type: The type of conveyancing service
            question_index: Index of the question being answered
            response: User's response (number or text)
            
        Returns:
            The option ID selected, or None if invalid
        """
        questions = ConditionalDocumentLogic.get_property_type_questions(service_type)
        
        if question_index >= len(questions):
            return None
        
        question = questions[question_index]
        options = question['options']
        
        # Try to parse as number
        try:
            choice_num = int(response.strip())
            if 1 <= choice_num <= len(options):
                return options[choice_num - 1]['id']
        except ValueError:
            pass
        
        # Try to match by text
        response_lower = response.lower().strip()
        for option in options:
            if response_lower in option['text'].lower() or option['text'].lower() in response_lower:
                return option['id']
        
        return None
    
    @staticmethod
    def get_conditional_document_explanation(
        document_id: str,
        is_required: bool
    ) -> str:
        """
        Get explanation for why a conditional document is or isn't required
        
        Args:
            document_id: The document identifier
            is_required: Whether the document is required
            
        Returns:
            Explanation message
        """
        explanations = {
            "levy_clearance": {
                True: "Levy clearance is required because this is a sectional title property.",
                False: "Levy clearance is not required for standalone properties."
            },
            "corrected_sg_diagram": {
                True: "Corrected SG diagram is required because this rectification involves spatial changes.",
                False: "Corrected SG diagram is not required for clerical error rectifications."
            },
            "joint_owner_ids": {
                True: "Multiple ID documents are required for each joint owner.",
                False: "Standard ID documentation for joint owners is sufficient."
            }
        }
        
        doc_explanations = explanations.get(document_id, {})
        return doc_explanations.get(is_required, "Document requirement based on property type.")


class PropertyTypeCollector:
    """Collects property type information from user responses"""
    
    def __init__(self, service_type: ServiceType):
        self.service_type = service_type
        self.questions = ConditionalDocumentLogic.get_property_type_questions(service_type)
        self.responses = {}
        self.current_question_index = 0
    
    def has_more_questions(self) -> bool:
        """Check if there are more questions to ask"""
        return self.current_question_index < len(self.questions)
    
    def get_current_question(self) -> Optional[Dict[str, Any]]:
        """Get the current question to ask"""
        if self.has_more_questions():
            return self.questions[self.current_question_index]
        return None
    
    def process_response(self, response: str) -> Dict[str, Any]:
        """
        Process user response to current question
        
        Args:
            response: User's response
            
        Returns:
            Dictionary with processing result
        """
        if not self.has_more_questions():
            return {"success": False, "error": "No more questions to answer"}
        
        # Parse response
        option_id = ConditionalDocumentLogic.parse_property_type_response(
            self.service_type,
            self.current_question_index,
            response
        )
        
        if not option_id:
            return {
                "success": False,
                "error": "Invalid response. Please choose a number from the options."
            }
        
        # Store response
        current_question = self.questions[self.current_question_index]
        self.responses[current_question['condition']] = option_id
        
        # Move to next question
        self.current_question_index += 1
        
        return {
            "success": True,
            "option_id": option_id,
            "has_more": self.has_more_questions()
        }
    
    def get_conditional_decisions(self) -> Dict[str, bool]:
        """Get final conditional document decisions"""
        return ConditionalDocumentLogic.evaluate_conditional_documents(
            self.service_type,
            self.responses
        )
    
    def get_all_responses(self) -> Dict[str, str]:
        """Get all user responses"""
        return self.responses


def evaluate_conditional_documents(
    service_type: ServiceType,
    user_responses: Dict[str, str]
) -> Dict[str, bool]:
    """
    Convenience function to evaluate conditional document requirements
    """
    return ConditionalDocumentLogic.evaluate_conditional_documents(
        service_type,
        user_responses
    )


def get_property_type_questions(service_type: ServiceType) -> List[Dict[str, Any]]:
    """
    Convenience function to get property type questions
    """
    return ConditionalDocumentLogic.get_property_type_questions(service_type)